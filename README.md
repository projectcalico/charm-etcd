etcd
====

A highly available configuration store in the spirit of zookeeper.

Etcd allows storing data in a distributed hierarchical database with observation.

Usage
-----

 $ juju deploy cs:~hazmat/trusty/etcd
 $ juju add-unit etcd


**Warning** Nodes cannot be removed cleanly from an etcd cluster at this time. Hopefully
this will exist for 0.4.0.


Charm Notes
-----------

Wrt to cluster management, We can't do the natural bit in juju which 
is to update a node with its set of peers. 

Once a node has joined the cluster the state of the system is kept
entirely within the raft log.

Quite a bit worse is the lack of ability to remove a node from the cluster, 
neither etcd nor influxdb exposes management capabilities against the cluster, which means
its. The raft library used by etcd and influxdb has some pathlogical behavior.
