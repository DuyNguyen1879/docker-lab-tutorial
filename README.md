# Docker Lab Tutorial

This is a lab tutorial to Docker and Linux containers. It covers theoretical background on Docker architecture and practical usage such as installation, configuration and monitoring of a Docker cluster. The tutorial refers to a setup made of hosts running CentOS 7.

## Content
1. [Linux Containers](./content/introduction.md)

2. [Start with Containers](./content/quickstart.md)
    * [Running an application](./content/quickstart.md#running-an-application)
    * [Working inside a container](./content/quickstart.md#working-inside-a-container)
    * [Inspecting a container](./content/quickstart.md#inspecting-a-container)

3. [Working with Images](./content/images.md)
     * [Getting started with images](./content/images.md#getting-started-with-images)
     * [Creating an image from a container](./content/images.md#creating-an-image-from-a-container)
     * [Creating an image from a Docker file](./content/images.md#creating-an-image-from-a-docker-file)
     * [Building your own images](./content/images.md#building-your-own-images)

4.  [Storage](./content/storage.md)
     * [Graph Drivers](./content/storage.md#graph-drivers)
     * [Persistent Volumes](./content/storage.md#persistent-volumes)
     * [Registry](./content/storage.md#registry)

5. [Networking](./content/networks.md)
     * [Default Networks](./content/networks.md#default-networks)
     * [User defined bridge networks](./content/networks.md#user-defined-bridge-networks)
     * [Using custom Docker networks](./content/networks.md#using-custom-docker-networks)
     * [Inter Containers Communication](./content/networks.md#inter-containers-communication)
     * [Embedded DNS Service](./content/networks.md#embedded-dns-service)
     * [MAC VLAN mode](./content/networks.md#mac-vlan-mode)

6. [Swarm Mode](./content/swarm-mode.md)
     * [Setup the Swarm](./content/swarm-mode.md#setup-the-swarm)
     * [Swarm Networking](./content/swarm-mode.md#swarm-networking)
     * [Deploying Services](./content/swarm-mode.md#deploying-services)
     * [Scaling Services](./content/swarm-mode.md#scaling-services)
     * [Routing Mesh](./content/swarm-mode.md#routing-mesh)
     * [Service Failover](./content/swarm-mode.md#service-failover)
     * [Service Networks](./content/swarm-mode.md#service-networks)
     * [Service Discovery](./content/swarm-mode.md#service-discovery)
     * [High Availability](./content/swarm-mode.md#high-availability)

7. [Applications Deployment](./content/applications.md)
      * [Application Stacks](./content/applications.md#applications-stacks)
      * [Service Mode](./content/applications.md#service-mode)
      * [Placement Constraints](./content/applications.md#placement-constraints)
      * [Updates Config](./content/applications.md#updates-config)
      * [Networks](./content/applications.md#networks)
      * [Volumes](./content/applications.md#volumes)

8. [Administration of the Docker Engine](./content/administration.md)
      * [Configure the engine](./content/administration.md#configure-the-engine)
      * [Securing the engine with TLS](./content/administration.md#securing-the-engine-with-tls)
      * [Accessing the engine with APIs](./content/administration.md#accessing-the-engine-with-apis)

## Disclaimer
This tutorial is for personal use only. This is just a lab guide, not a documentation for Docker, please go to their online
documentation sites for more details about what Docker is and how does it work.
