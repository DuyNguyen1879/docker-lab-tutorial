# Application Deployment
In this section we're going to walk through the application deployment in Docker Swarm Mode. With the introduction of Swarm Mode, the docker ecosystem is becoming a complete platform for devops, including the orchestration, multi host networking and applications deployment support.

   * [Application Stacks](#applications-stacks)
   * [Service Mode](#service-mode)
   * [Placement Constraints](#placement-constraints)
   * [Updates Config](#updates-config)
   * [Networks](#networks)
   * [Volumes](#volumes)

## Application Stacks
A stack is a collection of services that make up an application in a specific environment. A stack file is a file in yaml format that defines one or more services and how they are linked each other. Stacks are a convenient way to automatically deploy multiple services that are linked to each other, without needing to define each one separately.

Also, stack files define environment variables, deployment tags, the number of containers, and related environment-specific configurations like networks and shared volumes.

Here a simple example of a two-tier application made of a nodejs web server running on port 8080 and a proxy in front of it running on the port 80. The two services are linked via an internal overlay network.

Here the stack definition
```yaml
---
version: "3"
services:

  proxy:
    image: docker.io/kalise/http-proxy-server:latest
    ports:
      - "80:80"
    environment:
      REMOTE_PORT: 8080
      REMOTE_SERVER: nodejs
    networks:
      - application_network
    deploy:
      replicas: 1
      update_config:
        parallelism: 1
        delay: 30s
        failure_action: pause
        max_failure_ratio: 0
      restart_policy:
        condition: on-failure
      placement:
        constraints: [node.role == worker]

  nodejs:
    image: docker.io/kalise/nodejs-web-app:latest
    environment:
      MESSAGE: 'Hello Docker Swarm'
    networks:
      - application_network
    volumes:
      - log-volume:/var/log:rw
    deploy:
      mode: replicated
      replicas: 2
      update_config:
        parallelism: 1
        delay: 30s
        failure_action: pause
        max_failure_ratio: 0
      restart_policy:
        condition: on-failure
      placement:
        constraints: [node.role == worker]

volumes:
  log-volume:
    driver: local

networks:
  application_network:
    driver: overlay
    driver_opts:
      com.docker.network.driver.overlay.vxlanid_list: 9000
    ipam:
     driver: default
     config:
       - subnet: 172.128.1.0/24
```

There are three main section in the file above: ``services``, ``volumes``, and ``networks``. 

Starting from the services section, let's to detail all the options:

  * ``image`` option tells the image to be used by the service
  * ``ports`` option defines the port mapping 
  * ``environment`` option lists the env variables as defined in the related Dockerfile
  * ``networks`` option says the networks to which the containers are attached
  * ``volumes`` option lists the volumes as defined in the related Dockerfile
  * ``deploy`` option defines the deployng criteria, including replicas, restart options, update and placement policy

On the manager node, deploy the stack above
```
[root@swarm00 ~]# docker stack deploy --compose-file nodejs-app-stack.yml myapp
Creating network myapp_internal
Creating service myapp_nodejs
Creating service myapp_proxy

[root@swarm00 ~]# docker stack list
NAME   SERVICES
myapp  2

[root@swarm00 ~]# docker stack services myapp
ID            NAME          MODE        REPLICAS  IMAGE
38decu8yxubf  myapp_nodejs  replicated  2/2       docker.io/kalise/nodejs-web-app:latest
d5dpzidowg31  myapp_proxy   replicated  1/1       docker.io/kalise/http-proxy-server:latest

[root@swarm00 ~]# docker stack ps myapp
ID            NAME            IMAGE                                      NODE     DESIRED STATE  CURRENT STATE           
ztjwvthbckr6  myapp_proxy.1   docker.io/kalise/http-proxy-server:latest  swarm02  Running        Running 38 seconds ago
6cxjz59qgmel  myapp_nodejs.1  docker.io/kalise/nodejs-web-app:latest     swarm01  Running        Running 40 seconds ago
xgtr58ildc0m  myapp_nodejs.2  docker.io/kalise/nodejs-web-app:latest     swarm02  Running        Running 40 seconds ago
```

We can see our application made of two linked services and three containers since proxy service has been defined with replica 1 and nodejs service has been defined with replica 2. Also an overlay network has been created.

Let's to inspect the proxy and nodejs services
```
[root@swarm00 ~]# docker service list
ID            NAME          MODE        REPLICAS  IMAGE
tvom1dh8dr3h  myapp_proxy   replicated  1/1       docker.io/kalise/http-proxy-server:latest
xfme1hzygte0  myapp_nodejs  replicated  2/2       docker.io/kalise/nodejs-web-app:latest

[root@swarm00 ~]# docker service inspect myapp_proxy --pretty
[root@swarm00 ~]# docker service inspect myapp_nodejs --pretty
```

```yaml
ID:             sbuw8n2uw0oe9sn1yofkkyry6
Name:           myapp_proxy
Labels:
 com.docker.stack.namespace=myapp
Service Mode:   Replicated
 Replicas:      1
Placement:Contraints:   [node.role == worker]
UpdateConfig:
 Parallelism:   1
 Delay:         30s
 On failure:    pause
 Max failure ratio: 0
ContainerSpec:
 Image:         docker.io/kalise/http-proxy-server:latest
 Env:           REMOTE_PORT=8080 REMOTE_SERVER=nodejs
Resources:
Networks: 8dhnsemwghfc7olxqlnvypvou
Endpoint Mode:  vip
Ports:
 PublishedPort 80
  Protocol = tcp
  TargetPort = 80
```

```yaml
ID:             lqagfq2q2051d45mqxoj3or3e
Name:           myapp_nodejs
Labels:
 com.docker.stack.namespace=myapp
Service Mode:   Replicated
 Replicas:      2
UpdateStatus:
 State:         completed
 Started:       3 minutes
 Completed:     2 minutes
 Message:       update completed
Placement:Contraints:   [node.role == worker]
UpdateConfig:
 Parallelism:   1
 Delay:         30s
 On failure:    pause
 Max failure ratio: 0
ContainerSpec:
 Image:         docker.io/kalise/nodejs-web-app:2.4
 Env:           MESSAGE=Hello Docker Swarm
Mounts:
  Target = /var/log
   Source = myapp_log-volume
   ReadOnly = false
   Type = volume
Resources:
Networks: 8dhnsemwghfc7olxqlnvypvou
Endpoint Mode:  vip
```

Let's to go in details about services.

### Service Mode
Our services above are defined as replicated, meaning the number of containers that should be running at any given time. If, for any reason, the number of containers is lower than the expected, the swarm creates new containers to honor the replica set. The default is replicated ``mode: replicated``, the other option is global, meaning there is only one container for each node of the cluster.

To start a global service on each available node, use the ``mode: global`` option. Every time a new node becomes available, the scheduler places a task for the global service on the new node.

### Placement Constraints
Placement constraints force the swarm scheduling criteria. Our services above are both forced to be scheduled only on nodes having role of worker by the option ``[node.role == worker]``. Other options can be the node name, the node ID, the node name or some node labels. For example, we can force the swarm to schedule only on the node having a given hostname with the option ``[node.hostname == swarm02]``

### Updates Config
Updates configuration define how the service should be updated. This is useful for the so called "**rolling update**" of the service. During the lifetime of an application, some services need to be update, for example because the image changed. To update a service without an outage, swarm updates one or more container at a time, rather than taking down the entire service.

For example, this updates the nodejs service with a different image
```
[root@swarm00 ~]# docker service update \
   --image docker.io/kalise/nodejs-web-app:2.4 myapp_nodejs
```

We can see how this is happening by listing the running containers
```
[root@swarm00 ~]# docker service ps myapp_nodejs

ID            NAME                IMAGE                                   NODE     DESIRED STATE  CURRENT STATE            
4t335qd7qdon  myapp_nodejs.1      docker.io/kalise/nodejs-web-app:2.4     swarm02  Running        Running 18 seconds ago
z4b2pju5b1zy   \_ myapp_nodejs.1  docker.io/kalise/nodejs-web-app:latest  swarm02  Shutdown       Shutdown 19 seconds ago
bk1uezf88mzs  myapp_nodejs.2      docker.io/kalise/nodejs-web-app:2.4     swarm01  Running        Running 51 seconds ago
30nyy6yjj1r8   \_ myapp_nodejs.2  docker.io/kalise/nodejs-web-app:latest  swarm01  Shutdown       Shutdown 53 seconds ago
```

The swarm stopped the old containers running latest image and replaced with the specified image. The update is made one container at time. The following options configure the update strategy:

  * Parallelism:  the number of containers to update at time (1 in our case)
  * Delay: the time to wait between updating a group of containers (30 secs in our case)
  * On failure:  what to do if an update fails. One of continue or pause (pause, default in our case)
  * Max failure ratio: failure rate to tolerate during an update ( zero in our case)

## Networks
The top level networks key in the stack file, lets you specify how networks have to be created.
```yaml
...
networks:
  application_network:
    driver: overlay
    driver_opts:
      com.docker.network.driver.overlay.vxlanid_list: 9000
    ipam:
     driver: default
     config:
       - subnet: 172.128.1.0/24
...
```

Main options are:

  * Driver: the driver used for the network, usually bridge or overlay
  * Driver options: depending on the network driver
  * IPAM config: IP Address Management and related options
  * Internal Mode: if you want to create an externally isolated overlay network not connected to the default gateway network
  * External: when set to true, swarm will use an existing network, instead of create one called *stack-name_network_name*.
  * Labels: add metadata using either an array or a dictionary
  
The ``external`` option cannot be used in conjunction with the other network configuration options. Swarm will not to attempt to create the network, instead it will uses an existing network and will raise an error if such network does not exist.
```yaml
...
networks:
  existing_network_name:
    external: true
```

To create an external network outside the stack definition
```
[root@swarm00 ~]# docker network create \
  --driver overlay \
  --opt com.docker.network.driver.overlay.vxlanid_list=9002 \
  --subnet 172.128.0.0/24 \
  --gateway 172.128.0.1 \
  --label tenant=operation \
mynetwork
```

By default, when you connect a container to an overlay network, Docker also connects a bridge network to it to provide external connectivity. If you want to create an isolated overlay network, you can specify the internal option
```
[root@swarm00 ~]# docker network create \
  --driver overlay \
  --subnet 192.168.0.0/24 \
  --gateway 192.168.0.1 \
  --label tenant=test \
  --internal \
isolatednetwork
```

This is useful, for example, as backend network for services.

## Volumes
The top level volumes key lets you to define volumes for services. Volumes are directories or storage areas outside of the container’s filesystem where containers store reusable and shareable data that can persist even when containers are terminated. 
```yaml
...
volumes:
  log-volume:
    driver: local
...
```

Volumes, in their simplest form, are placed on the host fylesystem where containers are running. By default, they are in ``/var/lib/docker/volumes/`` directory if a different path is not specified. In the case above, the nodejs service mounts the volume ``/var/lib/docker/volumes/<stack>_log-volume`` into ``/var/log`` directory of the nodejs container. When the nodejs container terminates, data are still there. Volumes are mounted, by default, as read-write but it's possible to mount also as read-only. 

Inspecting the volume
```json
[
    {
        "Driver": "local",
        "Labels": {
            "com.docker.stack.namespace": "myapp"
        },
        "Mountpoint": "/var/lib/docker/volumes/myapp_log-volume/_data",
        "Name": "myapp_log-volume",
        "Options": {},
        "Scope": "local"
    }
]
```

Main options are:

  * Driver: the driver used for the network, default is local
  * Options: specific to a given driver
  * External: when set to true, swarm will use an existing volume, instead of create one called *stack-name_volume_name*.

The ``external`` option cannot be used in conjunction with the other volume configuration options. Swarm will not to attempt to create the volume, instead it will uses an existing volume and will raise an error if such volume does not exist.

To create an external volume outside the stack definition
```
[root@swarm00 ~]# docker volume create \
    --driver local \
    --label tenant=operations \
myvolume
```




