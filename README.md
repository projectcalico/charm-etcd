etcd
====


Charm Notes
===========

Wrt to cluster management, We can't do the natural bit in juju which 
is to update a node with its set of peers. 

Once a node has joined the cluster the state of the system is kept
entirely within the raft log.

Quite a bit worse is the lack of ability to remove a node from the cluster, 
neither etcd nor influxdb exposes management capabilities against the cluster, which means
    its The raft library used by etcd and influxdb has some
    pathlogical behavior.


Failure to start
- http://paste.ubuntu.com/7483775/