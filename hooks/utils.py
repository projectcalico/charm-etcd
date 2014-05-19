import bisect
import json
import os
import subprocess


CONFIG_PATH = '/opt/etcd/config'
TEMPLATE_PATH = os.path.join(
    os.environ.get('CHARM_DIR'), 'files', 'etcd.conf.template')


def write_config(
        peers=None, template_path=TEMPLATE_PATH, config_path=CONFIG_PATH):
    """
    """
    svc_config = json.loads(subprocess.check_output([
        "config-get", "--format=json"]))
    private_address = subprocess.check_output([
        "unit-get", "private-address"]).strip()

    template_data = {
        'name': os.environ.get('JUJU_UNIT_NAME'),
        'verbose': svc_config['debug'] and 'true' or 'false',
        'client_address': '0.0.0.0:4001',
        'peers': '[]',
        'peers_file': os.path.join(
            os.path.dirname(config_path), 'peers'),
        'peer_address': "%s:7001" % private_address}

    if peers:
        template_data['peers'] = "[%s]" % (
            ['"%s"' % s for s in peers])

    with open(template_path) as fh:
        template = fh.read()

    config = template % template_data

    if os.path.exists(config_path):
        with open(config_path) as fh:
            previous_config = fh.read()
    else:
        previous_config = ""

    if config == previous_config:
        return False

    with open(config_path, 'w') as fh:
        fh.write(config)

    print("update_config: starting etcd")
    subprocess.check_output(['service', 'etcd', 'restart'])
    return True


def update_peers(config_path=CONFIG_PATH):
    peers_path = os.path.join(
        os.path.dirname(config_path), 'peers')
    sentinel_path = os.path.join(
        os.path.dirname(config_path), 'sentinel')

    if os.path.exists(sentinel_path):
        print("peers already intialized (sentinel found), exiting")
        return

    if os.path.exists(peers_path):
        with open(peers_path) as fh:
            data = fh.read().strip()
    else:
        data = None
    # If we already have peers, left raft manage the ongoing
    # management. The sentinel path should normally take care of
    # this for us.
    if data:
        print("peers already intialized (peer data found) %s, exiting" % data)
        return

    peer_addrs = get_peer_addresses()
    if not peer_addrs:
        print("no peers found, exiting")
        return

    print("updating peers")
    with open(peers_path, 'w') as fh:
        fh.write(",".join(peer_addrs))

    # We have to reset the data on the node if its ever been started.
    subprocess.check_output(['service', 'etcd', 'stop'])
    subprocess.check_output(['rm', '-Rf', '/opt/etcd/var/'])
    os.mkdir('/opt/etcd/var')
    with open(sentinel_path, 'w') as fh:
        fh.write('initialized\n')

    subprocess.check_output(['service', 'etcd', 'start'])
    print("peers reconfigured, restarted etcd")


def get_peer_addresses():
    peer_rel = json.loads(subprocess.check_output([
        "relation-ids", "--format=json", "cluster"]))

    if not peer_rel:
        return []
    else:
        peer_rel = peer_rel[0]

    peer_ids = json.loads(subprocess.check_output([
        "relation-list", "-r", peer_rel, "--format=json"]))
    peer_ids.sort(lambda x, y: cmp(
        int(x.split('/')[-1]), int(y.split('/')[-1])))

    self_id = os.environ['JUJU_UNIT_NAME']

    # Only pick peers that are bigger than us in unit numbers
    idx = bisect.bisect_left(peer_ids, self_id)
    peers = []

    print("found peers %s of " % (peer_ids[:idx]), peer_ids)
    for pid in peer_ids[:idx]:
        data = subprocess.check_output([
            "relation-get", "-r", peer_rel, "--format=json", "-", pid])
        if not data:
            continue
        data = json.loads(data)
        peers.append("%s:7001" % data['private-address'])

    return peers
