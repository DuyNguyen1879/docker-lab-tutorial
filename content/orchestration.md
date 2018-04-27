# Orchestration
The native Docker orchestration engine called **Swarm** lets to have a complete all-built-in Docker cluster solution including orchestrator of containers and multi host networking. 

Main goals accomplished by an orchestation system like Swarm are:

  1. High Availability
  2. Scaling
  3. Load balancing

In this section, we are going to setup a simple three-nodes cluster based on Swarm.

  * [Setup the Swarm](#setup-the-swarm)
  * [Swarm Networking](#swarm-networking)
  * [Deploying Services](#deploying-services)
  * [Scaling Services](#scaling-services)
  * [Routing Mesh](#routing-mesh)
  * [Service Failover](#service-failover)
  * [Service Networks](#service-networks)
  * [Service Discovery](#service-discovery)
  * [Service Load Balancing](#service-load-balancing)
  * [High Availability](#high-availability)

A Swarm cluster of nodes is made of manager nodes and worker nodes:

  * **Managers**: they are nodes responsible for the control plane, i.e. the management of the cluster and services running on it
  * **Workers**: they are nodes running the user's services

Initially, our cluster is made of three nodes: one manager and only two workers. Please, note that in Swarm Mode, a node can be manager and worker at same time, i.e. a manager node can also run user's services. Multiple managers, with a minimum of three are recommended in production for high availability of the control plane. Swarm manager nodes use the [Raft](https://raft.github.io/) consensus algorithm to manage the swarm state. Raft requires a majority of managers, also called the quorum, to agree on proposed updates to the swarm and storing the same consistent state across all the manager nodes.

## Setup the Swarm
On all the three nodes, install the Docker engine. The following ports must be opened on the cluster back network:

  * TCP port 2377 for cluster management communications
  * TCP and UDP port 7946 for communication among nodes
  * UDP port 4789 for overlay network traffic

Also TCP port 2375 and 2376 (for TLS) should be opened on the front end network for Docker API service in case of remote management.

Make sure the Docker engine daemon is started on all the host machines
```
systemctl start docker
systemctl enable docker
systemctl status docker
```

Login tho the manager node and create the swarm
```
docker swarm init --advertise-addr ens33
```

The ``--advertise-addr ens33`` option tells to advertise on the cluster back network attached to physical interface ``ens33``. The other nodes in the swarm must be able to access the manager via this interface. Our setup uses a physical front network ``ens32`` for accessing the user's services and a separate physical back network ``ens33`` for clustering traffic among nodes.

Check the swarm node status
```
docker node list
ID                           HOSTNAME  STATUS  AVAILABILITY  MANAGER STATUS
tkxuxun03da7y2bozka50mpxi *  swarm00   Ready   Active        Leader
```

To add other nodes to the cluster, as worker nodes, we need for a token from the swarm manager

```
docker swarm join-token worker
To add a worker to this swarm, run the following command:

    docker swarm join \
    --token SWMTKN-1-3mbvdd9cay5eobj2om2pg5bdnl22z0qntmvvvslzsyt14mhgro-2qdyke72teir2erm9tuezaudj \
    192.168.2.60:2377
```

Login to the other nodes and add them to the cluster
```
docker swarm join \
    --token SWMTKN-1-3mbvdd9cay5eobj2om2pg5bdnl22z0qntmvvvslzsyt14mhgro-2qdyke72teir2erm9tuezaudj \
    192.168.2.60:2377

This node joined a swarm as a worker.
```

On the manager, check the swarm
```
docker node list
ID                           HOSTNAME  STATUS  AVAILABILITY  MANAGER STATUS
ickjus9bta1julsad2ls3paum    swarm01   Ready   Active
ryc6zlbxrhvblc7lk8pl3jsva    swarm02   Ready   Active
tkxuxun03da7y2bozka50mpxi *  swarm00   Ready   Active        Leader
```

Worker nodes can be promoted to manager role as following
```
docker node promote swarm01 swarm02

docker node list

ID                           HOSTNAME  STATUS  AVAILABILITY  MANAGER STATUS
3kru4v3w3lezys0tc9cnoczou *  swarm00   Ready   Active        Leader
e2kqucdbmkzm5ks6s2pciyg9v    swarm01   Ready   Active        Reachable
mdmnfom70hh86go8up5zl272y    swarm02   Ready   Active        Reachable
```

Also nodes can be directly added as manager by getting the token from an existing manager
```
docker swarm join-token manager
To add a manager to this swarm, run the following command:

    docker swarm join \
    --token SWMTKN-1-06y3xg5vjkh0tzla9fodgp6zrzsqqus8974b75umbvxeemwds9-1dlmdl3jxiz27ptggus4d9plg \
    10.10.10.60:2377
```

and running the join command on the new node
```
[root@swarm09 ~]# docker swarm join \
    --token SWMTKN-1-06y3xg5vjkh0tzla9fodgp6zrzsqqus8974b75umbvxeemwds9-1dlmdl3jxiz27ptggus4d9plg \
    10.10.10.60:2377
```

Adding manager nodes to a swarm, pay attention to the datacenter topology where to place them. For optimal high-availability, distribute manager nodes across a minimum of 3 availability zones to support failures of an entire set of machines.


To demote a node from manager to a worker
```
run docker node demote swarm02
```

To remove the node from the swarm
```
run docker node rm swarm01
```

To rejoin the node to the swarm with a fresh state
```
docker swarm join swarm01
```

In production, consider to run user's services only on worker nodes to avoid resources starvation on CPU and memory. To avoid interference between manager operations and user's services, you can *drain* a manager node to make it unavailable for services
```
docker node update --availability drain swarm00
ID                           HOSTNAME  STATUS  AVAILABILITY  MANAGER STATUS
3kru4v3w3lezys0tc9cnoczou *  swarm00   Ready   Drain         Leader
e2kqucdbmkzm5ks6s2pciyg9v    swarm01   Ready   Active        Reachable
mdmnfom70hh86go8up5zl272y    swarm02   Ready   Active        Reachable
```

When draining a node, the scheduler reassigns any user's services running on the node to other available worker nodes in the cluster also preventing the scheduler from assigning other services to that node.

If you want only troubleshoot a node without moving existing services, you can simply *pause* the node
```
docker node update --availability pause swarm00
ID                           HOSTNAME  STATUS  AVAILABILITY  MANAGER STATUS
3kru4v3w3lezys0tc9cnoczou *  swarm00   Ready   Pause         Leader
e2kqucdbmkzm5ks6s2pciyg9v    swarm01   Ready   Active        Reachable
mdmnfom70hh86go8up5zl272y    swarm02   Ready   Active        Reachable
```

To move things back, *active* the node
```
docker node update --availability pause swarm00
ID                           HOSTNAME  STATUS  AVAILABILITY  MANAGER STATUS
3kru4v3w3lezys0tc9cnoczou *  swarm00   Ready   Active        Leader
e2kqucdbmkzm5ks6s2pciyg9v    swarm01   Ready   Active        Reachable
mdmnfom70hh86go8up5zl272y    swarm02   Ready   Active        Reachable
```

## Swarm networking
Swarm mode setup creates a networking layout based on the overlay network driver. An overlay network is a network that is built on top of another network. Nodes in the overlay network can be connected by virtual or logical links, each of which corresponds to a path through one or more physical links in the underlying network.

Swarm mode leverages on the overlay networks to make all containers running on any node in the cluster as belonging to se same L2 network. Once activated, the swarm creates an overlay layout to connect all containers each other, no matter on which node the container is running. In this section, we're going to see in detail how this layout works. Swarm overlay networks are based on **VxLAN** technology.

Login to one of the node and check the networks
```
docker network list
NETWORK ID          NAME                DRIVER              SCOPE
862ce491c4d4        bridge              bridge              local
e73fde81ef50        docker_gwbridge     bridge              local
f0c9ed46f0b6        host                host                local
1qc6vhwhaeqn        ingress             overlay             swarm
eaef890efed3        none                null                local
```

We see an overlay network called ``ingress`` and a gateway bridge network called ``docker_gwbridge``. Let's start to inspect the overlay first
```
docker network inspect ingress
```

```json
[
    {
        "Name": "ingress",
        "Id": "1qc6vhwhaeqn0n9z2hdlawz72",
        "Created": "2017-03-27T15:47:53.139535526+02:00",
        "Scope": "swarm",
        "Driver": "overlay",
        "EnableIPv6": false,
        "IPAM": {
            "Driver": "default",
            "Options": null,
            "Config": [
                {
                    "Subnet": "10.255.0.0/16",
                    "Gateway": "10.255.0.1"
                }
            ]
        },
        "Internal": false,
        "Attachable": false,
        "Containers": {
            "ingress-sbox": {
                "Name": "ingress-endpoint",
                "EndpointID": "c8295e304e17f569575a6c0ba35c0d41a25515672776cf2da95f3715096ba442",
                "MacAddress": "02:42:0a:ff:00:03",
                "IPv4Address": "10.255.0.3/16",
                "IPv6Address": ""
            }
        },
        "Options": {
            "com.docker.network.driver.overlay.vxlanid_list": "4096"
        },
        "Labels": {},
        "Peers": [
            {
                "Name": "swarm00-a73dffac9ac0",
                "IP": "192.168.2.60"
            },
            {
                "Name": "swarm01-5bed1d4ed40a",
                "IP": "192.168.2.61"
            },
            {
                "Name": "swarm02-c97504fdbbf3",
                "IP": "192.168.2.62"
            }
        ]
    }
]
```

On this network having address space ``10.255.0.0/16``, there is a container called ``ingress-sbox``. This container is a special container created automatically by the swarm on each node of the cluster.

Now, inspect the gateway bridge network
```
docker network inspect docker_gwbridge
```

```json
[
    {
        "Name": "docker_gwbridge",
        "Id": "e73fde81ef50f8bc38516ff0545be26a150af8a4020fbc4ff07b5bb5050db84f",
        "Created": "2017-03-14T16:56:46.874874148+01:00",
        "Scope": "local",
        "Driver": "bridge",
        "EnableIPv6": false,
        "IPAM": {
            "Driver": "default",
            "Options": null,
            "Config": [
                {
                    "Subnet": "172.18.0.0/16",
                    "Gateway": "172.18.0.1"
                }
            ]
        },
        "Internal": false,
        "Attachable": false,
        "Containers": {
            "ingress-sbox": {
                "Name": "gateway_ingress-sbox",
                "EndpointID": "ee7552c5fd805e4f186eeb3d2ccf0576abdf0fca00c53f07cbb33d1a399610bc",
                "MacAddress": "02:42:ac:12:00:02",
                "IPv4Address": "172.18.0.2/16",
                "IPv6Address": ""
            }
        },
        "Options": {
            "com.docker.network.bridge.enable_icc": "false",
            "com.docker.network.bridge.enable_ip_masquerade": "true",
            "com.docker.network.bridge.name": "docker_gwbridge"
        },
        "Labels": {}
    }
]
```

On this network having address space ``172.18.0.0/16``, there is a container called ``gateway_ingress-sbox``. Checking the network namespaces

```
ip netns list
1-1qc6vhwhae (id: 1)
ingress_sbox (id: 2)
```

there are two namespaces. Checking the interface on the namespace called ``ingress_sbox``, we see it has two interfaces
```
ip netns exec ingress_sbox ip addr

...
51: eth0@if52: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue state UP
    link/ether 02:42:0a:ff:00:03 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet 10.255.0.3/16 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 fe80::42:aff:feff:3/64 scope link
       valid_lft forever preferred_lft forever

53: eth1@if54: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP
    link/ether 02:42:ac:12:00:02 brd ff:ff:ff:ff:ff:ff link-netnsid 1
    inet 172.18.0.2/16 scope global eth1
       valid_lft forever preferred_lft forever
    inet6 fe80::42:acff:fe12:2/64 scope link
       valid_lft forever preferred_lft forever
```

the first interface ``eth0`` on the ingress overlay network and the ``eth1`` on the gateway bridge network. What's the role of this namespace and of the ingress overlay network? The scope of the ingress namespace sandbox is to provide the entry point to expose services on the outer world. We'll see it in action when deploying some services on the cluster.

Back to the other namespace and check the interfaces
```
ip netns exec 1-1qc6vhwhae ip addr

1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN qlen 1
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever

2: br0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue state UP
    link/ether 76:18:82:e1:ff:26 brd ff:ff:ff:ff:ff:ff
    inet 10.255.0.1/16 scope global br0
       valid_lft forever preferred_lft forever
    inet6 fe80::c8cf:56ff:fec9:4d93/64 scope link
       valid_lft forever preferred_lft forever

50: vxlan1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue master br0 state UNKNOWN
    link/ether a2:9e:a4:4f:3b:1b brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet6 fe80::a09e:a4ff:fe4f:3b1b/64 scope link
       valid_lft forever preferred_lft forever

52: veth2@if51: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1450 qdisc noqueue master br0 state UP
    link/ether 76:18:82:e1:ff:26 brd ff:ff:ff:ff:ff:ff link-netnsid 1
    inet6 fe80::7418:82ff:fee1:ff26/64 scope link
       valid_lft forever preferred_lft forever
```

This namespace is a bridge for the overlay network. It is the gateway for all container to reach all other containers on the same overlay network.

Here the setup

![](../img/swarm.png?raw=true)

As we can see, the swarm create an overlay network covering all nodes in the cluster as they where on the same logical L2 network.


## Deploying services
In Swarm mode, a service is an abstraction to make containers alway reachable, no matter on which node they are running. In this section, we're going to deploy a simple application made of a nodejs web service. This service listen on the port 8080 and answers with a greating message from its bound IP address. To make this service available on the external world, we'll map its 8080 port to the host port 80.

On the master node, create the service
```
docker service create \
  --replicas 1 \
  --name nodejs \
  --publish 80:8080 \
  --constraint 'node.role==worker' \
kalise/nodejs-web-app:latest
```

With the command above, we told swarm to create a service called ``nodejs`` provided by a single container, i.e. ``replicas 1`` based on the image ``kalise/nodejs-web-app:latest``. We mapped the listening port ``8080`` to the exposed port to ``80``. also we force the container to run exclusively on worker nodes.

List the service
```
docker service list
ID            NAME    MODE        REPLICAS  IMAGE
lo6p4xrhlz3n  nodejs  replicated  1/1       kalise/nodejs-web-app:latest

docker service ps nodejs
ID            NAME      IMAGE                         NODE     DESIRED STATE  CURRENT STATE           ERROR  PORTS
uf9cr96onyh6  nodejs.1  kalise/nodejs-web-app:latest  swarm01  Running        Running 2 minutes ago
```

And inspect the just created service
```
docker service inspect --pretty nodejs
```

```yaml
ID:             lo6p4xrhlz3nnlo06yg5yn1jy
Name:           nodejs
Service Mode:   Replicated
 Replicas:      1
Placement:Contraints:   [node.role==worker]
UpdateConfig:
 Parallelism:   1
 On failure:    pause
 Max failure ratio: 0
ContainerSpec:
 Image:         kalise/nodejs-web-app:latest
Resources:
Endpoint Mode:  vip
Ports:
 PublishedPort 80
  Protocol = tcp
  TargetPort = 8080
```

The service is backed by a container running on worker node ``swarm01``.

Login to this worker node and inspect the related namespace
```
ip netns
ff939e571cc9 (id: 3)
1-1qc6vhwhae (id: 1)
ingress_sbox (id: 2)

ip netns exec 97c81c75e70a ifconfig
eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1450
        inet 10.255.0.7  netmask 255.255.0.0  broadcast 0.0.0.0
        inet6 fe80::42:aff:feff:7  prefixlen 64  scopeid 0x20<link>
        ether 02:42:0a:ff:00:07  txqueuelen 0  (Ethernet)

eth1: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 172.18.0.3  netmask 255.255.0.0  broadcast 0.0.0.0
        inet6 fe80::42:acff:fe12:3  prefixlen 64  scopeid 0x20<link>
        ether 02:42:ac:12:00:03  txqueuelen 0  (Ethernet)
...

```

The container has the interface ``eth0`` attached to the ingress overlay network and the interface ``eth1`` attached to the gateway bridge network. Let's to confim this by inspecting the two networks

```
docker network list
NETWORK ID          NAME                DRIVER              SCOPE
5b47cdaf82b1        bridge              bridge              local
18ef9a1c2e08        docker_gwbridge     bridge              local
5f03d7b5240a        host                host                local
1qc6vhwhaeqn        ingress             overlay             swarm
3cd5989ee74c        none                null                local
```

The overlay ingress network
```
docker network inspect ingress
```
```json
[
    {
        "Name": "ingress",
        "Id": "1qc6vhwhaeqn0n9z2hdlawz72",
        "Created": "2017-03-27T15:50:28.680582431+02:00",
        "Scope": "swarm",
        "Driver": "overlay",
        "EnableIPv6": false,
        "IPAM": {
            "Driver": "default",
            "Options": null,
            "Config": [
                {
                    "Subnet": "10.255.0.0/16",
                    "Gateway": "10.255.0.1"
                }
            ]
        },
        "Internal": false,
        "Attachable": false,
        "Containers": {
            "c5ce0bf928def33a6e7680df34fe7a57aeee74f4b9f3270b8d59a39c03eacc53": {
                "Name": "nodejs.1.uf9cr96onyh6cw9ii97pgx5i4",
                "EndpointID": "4213a7e8373a538f3816d12830449aed032d442c00eb0670ee4f881f819ee2f7",
                "MacAddress": "02:42:0a:ff:00:07",
                "IPv4Address": "10.255.0.7/16",
                "IPv6Address": ""
            },
            "ingress-sbox": {
                "Name": "ingress-endpoint",
                "EndpointID": "7491408342eb79dc0030f5e1b564ab54719532449427b9f6fb57ff33daeb3336",
                "MacAddress": "02:42:0a:ff:00:04",
                "IPv4Address": "10.255.0.4/16",
                "IPv6Address": ""
            }
        },
        "Options": {
            "com.docker.network.driver.overlay.vxlanid_list": "4096"
        },
        "Labels": {},
        "Peers": [
            {
                "Name": "swarm01-5bed1d4ed40a",
                "IP": "192.168.2.61"
            },
            {
                "Name": "swarm00-a73dffac9ac0",
                "IP": "192.168.2.60"
            },
            {
                "Name": "swarm02-c97504fdbbf3",
                "IP": "192.168.2.62"
            }
        ]
    }
]
```

The gateway bridge network
```
docker network inspect docker_gwbridge
```

```json
[
    {
        "Name": "docker_gwbridge",
        "Id": "18ef9a1c2e0885ce3c0e20498277df68e30f91f5b1912068417d9d19c98e2ef7",
        "Created": "2017-03-16T17:53:58.301607018+01:00",
        "Scope": "local",
        "Driver": "bridge",
        "EnableIPv6": false,
        "IPAM": {
            "Driver": "default",
            "Options": null,
            "Config": [
                {
                    "Subnet": "172.18.0.0/16",
                    "Gateway": "172.18.0.1"
                }
            ]
        },
        "Internal": false,
        "Attachable": false,
        "Containers": {
            "c5ce0bf928def33a6e7680df34fe7a57aeee74f4b9f3270b8d59a39c03eacc53": {
                "Name": "gateway_c5ce0bf928de",
                "EndpointID": "c8261f30b1177a2da884ce044c6e21b56f6a4e883b48c012793157ef6800aa19",
                "MacAddress": "02:42:ac:12:00:03",
                "IPv4Address": "172.18.0.3/16",
                "IPv6Address": ""
            },
            "ingress-sbox": {
                "Name": "gateway_ingress-sbox",
                "EndpointID": "406a79b5f97ea47a78eefb6c4902cf97338373a979f1ac42c16ada439852a54d",
                "MacAddress": "02:42:ac:12:00:02",
                "IPv4Address": "172.18.0.2/16",
                "IPv6Address": ""
            }
        },
        "Options": {
            "com.docker.network.bridge.enable_icc": "false",
            "com.docker.network.bridge.enable_ip_masquerade": "true",
            "com.docker.network.bridge.name": "docker_gwbridge"
        },
        "Labels": {}
    }
]
```

So the network layout should be like this

![](../img/swarm-layout-01.png?raw=true)

We see the gateway bridge network as ingress point for all requests to the exposed nodejs service ``curl http://swarm01:80``. These requests are handled by the ingress sandbox on each node and then dispatched on the nodejs container via the overlay network. This is accomplished by a complex set of iptables chain.

The iptables on that host intercept the request and translate to the ingress sandbox address on the gateway bridge network, i.e. ``172.18.0.2:80``. Then the request comes to the sandbox gateway that will traslate it to IP ``10.255.0.4``, which is the IP address of its interface on the ingress overlay network. 

At this point, the request is dispatched to the destination container on the overlay network. Swarm uses the embedded load balancer implementation in the Linux kernel called **IPVS**. To check the configuration of the IPVS, we need to install before the admin tool ``ipvsadm``.

```
yum install ipvsadm -y

ip netns exec ingress_sbox ipvsadm -ln
IP Virtual Server version 1.2.1 (size=4096)
Prot LocalAddress:Port Scheduler Flags
  -> RemoteAddress:Port           Forward Weight ActiveConn InActConn
FWM  263 rr
  -> 10.255.0.7:0                 Masq    1      0          0
```

The configuration above is telling the IPVS load balancer to forward requests to the IP ``10.255.0.7`` that is the IP of the nodejs container on the other worker node. It’s the only backend server for our internal load balancer. Requests reach the backend via the overlay network.

## Scaling Services
What happens when scaling the service to have more than one container? Swarm Mode has the feature to scale out the containers backing a service. Let's to scale our service to have 2 containers

On the master node,
```
docker service scale nodejs=2
nodejs scaled to 2

docker service ps nodejs
ID            NAME      IMAGE                         NODE     DESIRED STATE  CURRENT STATE           ERROR  PORTS
l4ubi2w5cijm  nodejs.1  kalise/nodejs-web-app:latest  swarm01  Running        Running 2 hours ago
rcftpr36e6or  nodejs.2  kalise/nodejs-web-app:latest  swarm02  Running        Running 1 minutes ago
```

We see a new container running on the ``swarm02`` worker node. Login to this node and check the container interfaces

```
ip netns list
83ec387bc9f1 (id: 3)
1-1qc6vhwhae (id: 1)
ingress_sbox (id: 2)

ip netns exec 83ec387bc9f1 ifconfig
eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1450
        inet 10.255.0.8  netmask 255.255.0.0  broadcast 0.0.0.0
        inet6 fe80::42:aff:feff:8  prefixlen 64  scopeid 0x20<link>
        ether 02:42:0a:ff:00:08  txqueuelen 0  (Ethernet)

eth1: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 172.18.0.3  netmask 255.255.0.0  broadcast 0.0.0.0
        inet6 fe80::42:acff:fe12:3  prefixlen 64  scopeid 0x20<link>
        ether 02:42:ac:12:00:03  txqueuelen 0  (Ethernet)
...
```

This container has IP ``10.255.0.8`` on the ingress overlay network.

Back to the master node, check what happened to the IPVS load balancer configuration
```
ip netns exec ingress_sbox ipvsadm -ln
IP Virtual Server version 1.2.1 (size=4096)
Prot LocalAddress:Port Scheduler Flags
  -> RemoteAddress:Port           Forward Weight ActiveConn InActConn
FWM  263 rr
  -> 10.255.0.7:0                 Masq    1      0          0
  -> 10.255.0.8:0                 Masq    1      0          0
```


As we can see the IPVS now has 2 backends, one for each container. We can test this by issuing requests to the host node
```
curl 10.10.10.60:80
Hello World! from 10.255.0.8

curl 10.10.10.60:80
Hello World! from 10.255.0.7

curl 10.10.10.60:80
Hello World! from 10.255.0.8
...
```

Clients requests are handled by IPVS in a round robin fashion.

Here the layout 

![](../img/swarm-layout-02.png?raw=true)


## Routing Mesh
All the nodes partecipating in a swarm, are able to route incoming requests from their Ingress Sandbox to the specified service, no matter which is the node running the service. This feature is called "**Routing Mesh**" and it is used to expose a service to the external world. For example, a request to the exposed nodejs service ``curl http://swarm00:80`` or ``curl http://swarm02:80`` will be handled by the IPVS on the nodes ``swarm00`` and ``swarm02`` respectively.

```
netstat -natp | grep 80
tcp6       0      0 :::80                   :::*                    LISTEN      488/docker-proxy

curl 10.10.10.60:80
Hello World! from 10.255.0.7
```

and
```
netstat -natp | grep 80
tcp6       0      0 :::80                   :::*                    LISTEN      488/docker-proxy

curl 10.10.10.61:80
Hello World! from 10.255.0.7
```

and
```
netstat -natp | grep 80
tcp6       0      0 :::80                   :::*                    LISTEN      488/docker-proxy

curl 10.10.10.62:80
Hello World! from 10.255.0.7
```


Here the layout

![](../img/swarm-layout-03.png?raw=true)

Please, note that routing mesh is the default option. If you need your service to be exposed only on the node where it is actually running, you can force this with the ``--publish mode=host,target=<target_port>,published=<published_port>`` option during service creation. For example:
```
docker service create  \
          --replicas 1 \
          --name nodejs \
          --publish mode=host,target=8080,published=80 \
          --constraint 'node.hostname==node01' \
          kalise/nodejs-web-app:latest
```

We can see only worker node ``node01`` running the service is exposing the port
```
netstat -natp | grep 80


netstat -natp | grep 80
tcp6       0      0 :::80                   :::*                    LISTEN      488/docker-proxy

netstat -natp | grep 80

```

In general, routing mesh is the prefereable way to expose services.

## Service Failover
In this section we are going to explore how swarm handles a service failover. Single containers are not replaced if they get failed, deleted or terminated for some reason. To make things more robust, Swarm introduces the replica abstraction. A replica ensures that a service gets a specified number of running container "replicas" at any time. In other words, a replica makes sure that a service has always coontainers up and running, no matter what happens. If there are too many containers, it will kill some; if there are too few, it will start more.

Create a service with a replica 1
```
docker service create \
   --replicas 1 \
   --name nodejs \
   --publish 80:8080 \
   --constraint 'node.role==worker' \
   kalise/nodejs-web-app:latest

docker service ps nodejs
ID            NAME      IMAGE                         NODE     DESIRED STATE  CURRENT STATE           ERROR  PORTS
faapm76m2wgd  nodejs.1  kalise/nodejs-web-app:latest  swarm01  Running        Running 13 seconds ago

docker service inspect --pretty nodejs
```
```yaml
ID:             9xcryw8i2i2wvslejlj6yjwry
Name:           nodejs
Service Mode:   Replicated
 Replicas:      1
Placement:Contraints:   [node.role==worker]
UpdateConfig:
 Parallelism:   1
 On failure:    pause
 Max failure ratio: 0
ContainerSpec:
 Image:         kalise/nodejs-web-app:latest
Resources:
Endpoint Mode:  vip
Ports:
 PublishedPort 80
  Protocol = tcp
  TargetPort = 8080
```

Our service has replica 1  meaning it will get always 1 container, no matter what happens. In case of failure of the running container or the worker node or whatelse, swarm will make sure there will be always one running container.

To test this, let's to manually kill the running container. Login to the worker node where the container is running and kill it.
```
docker rm -f nodejs.1.faapm76m2wgdubylakmjnkwge
nodejs.1.faapm76m2wgdubylakmjnkwge

docker ps
CONTAINER ID        IMAGE   
```

Back to the manager node and check the status of the service
```
docker service ps nodejs
ID            NAME          IMAGE                         NODE     DESIRED STATE  CURRENT STATE          ERROR                        PORTS
lmeet488s78q  nodejs.1      kalise/nodejs-web-app:latest  swarm02  Running        Running 2 minutes ago
faapm76m2wgd   \_ nodejs.1  kalise/nodejs-web-app:latest  swarm01  Shutdown       Failed 3 minutes ago   "task: non-zero exit (137)"
```

We see the swarm detected the failure of the container running on node ``swarm01`` and then started a new container on the node ``swarm02`` to honor the number of replicas we set.

## Service Networks
The overlay network model permits swarm to create a complex layout of networks. In this section, we're going to deploy services on dedicated custom internal network. This is useful when we have to build multilayer applications made of different services. These services will reach each other via dedicated custom internal networks.

Create a new overlay network called ``internal``
```
docker network create --driver=overlay --subnet=172.30.0.0/24 --attachable internal

docker network list
NETWORK ID          NAME                DRIVER              SCOPE
6e035fb63823        bridge              bridge              local
e73fde81ef50        docker_gwbridge     bridge              local
f0c9ed46f0b6        host                host                local
1qc6vhwhaeqn        ingress             overlay             swarm
kq7sc5qu1wle        internal            overlay             swarm
eaef890efed3        none                null                local
```

The ``--attachable`` option enables manual container attachment on that network. We use it only for demo purpouse, normally we do not need to use it.

Inspecting the internal network just created

```json
[
    {
        "Name": "internal",
        "Id": "kq7sc5qu1wlelrat8wnqob2g2",
        "Created": "0001-01-01T00:00:00Z",
        "Scope": "swarm",
        "Driver": "overlay",
        "EnableIPv6": false,
        "IPAM": {
            "Driver": "default",
            "Options": null,
            "Config": [
                {
                    "Subnet": "172.30.0.0/24",
                    "Gateway": "172.30.0.1"
                }
            ]
        },
        "Internal": false,
        "Attachable": true,
        "Containers": null,
        "Options": {
            "com.docker.network.driver.overlay.vxlanid_list": "4097"
        },
        "Labels": null
    }
]
```

Then start a nodejs web service on this network
```
docker service create \
       --replicas 1 \
       --name nodejs \
       --network internal \
       --constraint 'node.role==worker' \
       kalise/nodejs-web-app:latest
```

Check where the service is running
```
docker service ps nodejs
ID            NAME      IMAGE                         NODE     DESIRED STATE  CURRENT STATE          ERROR  PORTS
2ceiqgqalqnu  nodejs.1  kalise/nodejs-web-app:latest  swarm01  Running        Running 5 minutes ago
```

Login to the worker node where service is running. By inspecting the internal network, we see the service container is attached to that network as expected.  

```json
...
        "Internal": false,
        "Attachable": false,
        "Containers": {
            "9b2e3c6c9bcb052a61263eaf696c7352ae33a95e441c604e9929e74d85d0ea1e": {
                "Name": "nodejs.1.o6fo1nik5sh23ju7f3d6n65ki",
                "EndpointID": "1e8471d06db53c6c789189e716af3c870093814ad62d29b4d6b5dba9da6fc4e3",
                "MacAddress": "02:42:ac:1e:00:03",
                "IPv4Address": "172.30.0.3/24",
                "IPv6Address": ""
            }
        },
        "Options": {
            "com.docker.network.driver.overlay.vxlanid_list": "4097"
        },
        "Labels": {},
...
```

Also the service container is attached to the gateway bridge network since it has to access the external world via NAT as per docker networking model
```json
...
        "Internal": false,
        "Attachable": false,
        "Containers": {
            "9b2e3c6c9bcb052a61263eaf696c7352ae33a95e441c604e9929e74d85d0ea1e": {
                "Name": "gateway_9b2e3c6c9bcb",
                "EndpointID": "1a1a6e3f2f27944f9af8980f6bfa26ff8d1a38b4641ac7368d966055f7245671",
                "MacAddress": "02:42:ac:12:00:03",
                "IPv4Address": "172.18.0.3/16",
                "IPv6Address": ""
            },
            "ingress-sbox": {
                "Name": "gateway_ingress-sbox",
                "EndpointID": "686c50270cbd251dd02acc73ffabdce77067ecf5dcf9e6e01552d2ca1eef5a65",
                "MacAddress": "02:42:ac:12:00:02",
                "IPv4Address": "172.18.0.2/16",
                "IPv6Address": ""
            }
        },
        "Options": {
            "com.docker.network.bridge.enable_icc": "false",
            "com.docker.network.bridge.enable_ip_masquerade": "true",
            "com.docker.network.bridge.name": "docker_gwbridge"
        },
        "Labels": {}
...
```

Our nodejs service is only reachable by only other services running on the internal network. To reach it, create another service, eg. busybox, on the same internal network
```
docker service create \
  --name busybox \
  --network internal \
  --constraint 'node.role==worker'  \
busybox:latest sleep 3000
```

Check where busybox service has its running container
```
docker service ps busybox
ID            NAME       IMAGE           NODE     DESIRED STATE  CURRENT STATE
1swg9p3myu38  busybox.1  busybox:latest  swarm02  Running        Running 10 seconds ago
```

Login to the busybox container and access the nodejs service
```
docker exec -it busybox.1 sh
/ #

/ # wget 172.30.0.3:8080 -O -
Connecting to 172.30.0.3:8080 (172.30.0.3:8080)
<html><head></head><body>Hello World! from 172.30.0.3</body></html>
```

However, the service is not reachable from the external world because we did not exposed it. To make it accessible from outside, login to the manager node and expose the service to an host port
```
docker service update nodejs --publish-add 80
```

Login to the worker node where service is running. By inspecting the ingress network, we see now the service container is attached on that network too. 
```json
...
        "Internal": false,
        "Attachable": false,
        "Containers": {
            "9b2e3c6c9bcb052a61263eaf696c7352ae33a95e441c604e9929e74d85d0ea1e": {
                "Name": "nodejs.1.o6fo1nik5sh23ju7f3d6n65ki",
                "EndpointID": "ddf9d3c61e0ea8d112006ea20caf70050a71cd20609e1b216f29baf7cdd6cf98",
                "MacAddress": "02:42:0a:ff:00:08",
                "IPv4Address": "10.255.0.8/16",
                "IPv6Address": ""
            },
            "ingress-sbox": {
                "Name": "ingress-endpoint",
                "EndpointID": "5eaa13364c6edbd1541f4401aa1ef275d2df7f659bda6e39647745a3f17e9c5d",
                "MacAddress": "02:42:0a:ff:00:06",
                "IPv4Address": "10.255.0.6/16",
                "IPv6Address": ""
            }
        },
        "Options": {
            "com.docker.network.driver.overlay.vxlanid_list": "4096"
        },
...
```
The reason for that is because we asked the swarm to expose the service on a public port 80. When a user's request reach the ingress sandbox, it will redirect the request to the service container via the ingress network as in the previous example.
```
wget swarm01:80 -O -
...
<html><head></head><body>Hello World! from 10.255.0.8</body></html>
```

If we want to hide the service container, simply detach the service from the host port
```
docker service update nodejs --publish-add 80
```

## Service Discovery
As for single host docker networking, the docker swarm uses embedded DNS to provide service discovery for containers running in a swarm. Docker Engine has an embedded DNS server ``nameserver 127.0.0.11`` that provides name resolution to all of the containers. Each container has a DNS resolver that forwards DNS queries to engine, which acts as a DNS server. Docker Engine then checks if the DNS query belongs to a container or service on each network that the requesting container belongs to. If it does, then Docker Engine looks up the IP address that matches a container or service's name in its key-value store and returns the IP address of the container or the  Virtual IP (VIP) associated to the service. Then it sends back the answer to the requester. In case of the service, the VIP is used for load balancing requests to container replicas providing the service.

Service discovery is network-scoped, meaning only containers that are on the same network - including on different hosts - can use the embedded DNS functionality. Containers not on the same network cannot resolve each other's addresses. If the destination container or service and the source container are not on the same network, Docker Engine forwards the DNS query to the external DNS server.

To test service discovery and load balancing, let's to create an internal overly network since service discovery does not work on the ingress overlay network

```
docker network create --driver=overlay --subnet=172.32.0.0/24 internal
```

Then create a nodejs web service with 2 replicas and attach it on the above network
```
docker service create  \
   --replicas 2 \
   --name nodejs \
   --publish 80:8080  \
   --network internal  \
   --constraint 'node.role==worker'  \
docker.io/kalise/nodejs-web-app:latest
```

Create another service, eg. busybox, on the same network
```
docker service create \
  --name busybox \
  --network internal \
  --constraint 'node.role==worker'  \
busybox:latest sleep 3000
```

Check where busybox service has its running container
```
docker service ps busybox
ID            NAME       IMAGE           NODE     DESIRED STATE  CURRENT STATE
1swg9p3myu38  busybox.1  busybox:latest  swarm02  Running        Running 10 seconds ago
```

Login to the busybox container and check the resolution of the nodejs service
```
docker exec -it busybox.1.1swg9p3myu38zzh1wmw8vylrd sh

/ # cat /etc/resolv.conf
search clastix.io
nameserver 127.0.0.11
options ndots:0

/ # ping nodejs
PING nodejs (172.32.0.2): 56 data bytes
64 bytes from 172.32.0.2: seq=0 ttl=64 time=0.085 ms
64 bytes from 172.32.0.2: seq=1 ttl=64 time=0.116 ms
^C
--- nodejs ping statistics ---
2 packets transmitted, 2 packets received, 0% packet loss
round-trip min/avg/max = 0.085/0.100/0.116 ms

/ # exit
```

The requests for ``nodejs`` host are resolved by the embedded DNS server ``nameserver 127.0.0.11`` with the Virtual IP ``172.32.0.2`` of the nodejs service. The Virtual IP of that service is internally load balanced to the individual container IP addresses. Container names are resolved as well, albeit directly to their IP addresses. An external hostname as ``docker.com`` does not exist as a service name in the internal network, so the request is forwarded to the external default DNS server on the host machine.

Traffic to the VIP is automatically sent to all running container replicas of that service across the overlay network. This approach avoids any client side load balancing because only a single IP is returned to the client. Docker engine takes care of routing and equally distributes the traffic across the healthy service container.

To get the VIP of a service, inspect it
```
docker service inspect nodejs
```

```json
...
            "Spec": {
                "Mode": "vip",
                "Ports": [
                    {
                        "Protocol": "tcp",
                        "TargetPort": 8080,
                        "PublishedPort": 80,
                        "PublishMode": "ingress"
                    }
                ]
            },
            "Ports": [
                {
                    "Protocol": "tcp",
                    "TargetPort": 8080,
                    "PublishedPort": 80,
                    "PublishMode": "ingress"
                }
            ],
            "VirtualIPs": [
                {
                    "NetworkID": "vcvqu78nxipjwqmr1ew170zzi",
                    "Addr": "10.255.0.5/16"
                },
                {
                    "NetworkID": "wh11rcyqwqgeqzfw7dfi19zrh",
                    "Addr": "172.32.0.2/24"
                }
            ]
...
```

## Service Load Balancing
With the routing mesh, the swarm is able to expose the service on each node of the cluster. However, load balancing is only limited to the cluster nodes. User can also configure an external application load balancer, e.g. HAProxy, to route requests from the web to a service published on port 80.

For example, you could have the following configuration ``/etc/haproxy/haproxy.cfg`` for the HAProxy load balancer.
```
global
        log /dev/log    local0
        log /dev/log    local1 notice
...snip...

# Configure HAProxy to listen on port 80
frontend http_front
   bind *:80
   stats uri /haproxy?stats
   default_backend http_back

# Configure HAProxy to route requests to swarm nodes on port 80
backend http_back
   balance roundrobin
   server swarm00 10.10.10.60:80 check
   server swarm01 10.10.10.61:80 check
   server swarm02 10.10.10.62:80 check
```

When users access the HAProxy load balancer on port 80, it forwards requests to nodes in the swarm. The swarm routing mesh feature routes the requests to the containers through the internal IPV load balancer. If, for any reason, the swarm scheduler dispatches the container to a different node, the system admin don’t need to reconfigure the load balancer.

## Cluster High Availability
A Swarm cluster with only a manager node is a single point of failure of the cluster control plane. When the control plane is no more available, user's services are still working on worker nodes but the sysadmin is no more able to control the cluster. Also, if something wrong happens on worker nodes, the cluster itself is not able to control the user's services. For this reasons, it is strongly recommended to protect the control plane with multiple managers.

An odd number of managers in the swarm cluster is required to support manager node failures. Having an odd number of managers ensures that during an outage, the cluster quorum remains available to process requests when an outage occurs and the cluster is partitioned into two separate sets. A Swarm cluster tolerates up to (N-1)/2 failures and requires a majority or quorum of (N/2)+1 members to agree on values proposed to the cluster.

According to the [Raft](https://raft.github.io/) alghoritm, the swarm cluster start a leader election process when the cluster is formed. The leader is in charge of keep all changes to the system by taking a distributed consensus among other manager nodes.

With a single manager, we just have the leader 
```
docker node list
ID                           HOSTNAME  STATUS  AVAILABILITY  MANAGER STATUS
b07ejkr444dm5bsbmey4hrd2r *  swarm00   Ready   Active        Leader
q5wjauy7i4fr7ictcsu2wkl68    swarm01   Ready   Active        
r8zwpsx1rczpmoxk11i6fuk21    swarm02   Ready   Active        
```

By promoting the other nodes to master role, we still have the same leader
```
docker node promote swarm01 swarm02

docker node list
ID                           HOSTNAME  STATUS  AVAILABILITY  MANAGER STATUS
b07ejkr444dm5bsbmey4hrd2r *  swarm00   Ready   Active        Leader
q5wjauy7i4fr7ictcsu2wkl68    swarm01   Ready   Active        Reachable
r8zwpsx1rczpmoxk11i6fuk21    swarm02   Ready   Active        Reachable
```

We have the leader election process restart if the current leader goes down for some reason and a new manager node becomes the leader 
```
systemctl restart docker

docker node list
ID                           HOSTNAME  STATUS  AVAILABILITY  MANAGER STATUS
b07ejkr444dm5bsbmey4hrd2r *  swarm00   Ready   Active        Reachable
q5wjauy7i4fr7ictcsu2wkl68    swarm01   Ready   Active        Reachable
r8zwpsx1rczpmoxk11i6fuk21    swarm02   Ready   Active        Leader
```

There is no limit on the number of manager nodes. The decision about how many manager nodes to implement is a trade-off between performance and fault-tolerance. Why not have all nodes in a cluster to be managers? Intuitively, it is harder to reach consensus in large set of nodes since all writes have to go to and be acknowledged by all nodes. This leads to more network traffic and more latency.
