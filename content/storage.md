# Container Storage
Docker separates storage requirements into three categories:

   * [Graph Drivers](#graph-drivers) for container run storage
   * [Persistent Volumes](#persistent-volumes) for persistent data storage
   * [Registry](#registry) for image storage

This section will explore in further detail, each of these three distinct storage tiers: graph driver storage, volume storage, and registry storage.

## Graph Drivers
Storage used for reading image filesystem layers from a running container state typically require IOPS and other read/write intensive operations, which leads to performance being a key storage metric. Docker adopted a layered storage architecture for the images and containers. A layered file system is made of many separate layers allowing images to be constructed and deconstructed as needed instead of creating a large, monolithic image.

Supported layered file systems are:
  
   * device mapper
   * btrfs
   * aufs
   * overlay

The Overlay file system is becoming default choice for all Linux distributions. However, on CentOS/RHEL it is still reccomended to use device mapper.

To check the storage layered file system, inspect the docker engine
```
docker system info | grep -i "Storage Driver"
Storage Driver: overlay
```

When a docker image is pulled from the registry, the engine download all the dependent layers to the host machine. When the container is launched from an image comprised of many layers, docker uses the **Copy-on-Write** capability of the layered file system to add a read write working directory on top of existing read only layers. 

![](../img/container-layers.jpg?raw=true)

Pull an ubuntu image from the Docker Hub
```
[root@clastix00 ~]# docker pull ubuntu:15.04
15.04: Pulling from library/ubuntu
9502adfba7f1: Pull complete
4332ffb06e4b: Pull complete
2f937cc07b5f: Pull complete
a3ed95caeb02: Pull complete
Digest: sha256:2fb27e433b3ecccea2a14e794875b086711f5d49953ef173d8a03e8707f1510f
Status: Downloaded newer image for ubuntu:15.04

[root@host ~]# docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
ubuntu              15.04               d1b55fd07600        14 months ago       131 MB
```

Image layers are placed in the local host storage area 
```
[root@host ~]# ll /var/lib/docker/overlay
total 0
drwx------ 3 root root 17 Apr 11 13:25 863324a4a64a561da3d5f1623040dd292d079a810fd8767296ae6d6f7561b902
drwx------ 3 root root 17 Apr 11 13:25 8c56e1d6822091e11edfb1b14b586ba29788de5bcdaa00234a0b5dfa1432ff7b
drwx------ 3 root root 17 Apr 11 13:34 c154bf1e4f992ce599b497da5fb554e52d32127eb4ecc3a141cbf48331788dba
drwx------ 3 root root 17 Apr 11 13:25 e8ef46122ade93666dd7c1218580063d0f4e0869f940707b2a3cdbf7ea83e9cb
```

When a container starts, this initial read write layer is empty until changes are made by the running container process. When a process attempts to write a new file or update an existing one, the filesystem creates a copy of the new file on the upper writeable layer.

```
[root@host ~]# docker run --name ubuntu -it ubuntu:15.04
root@3b927950034f:/# useradd adriano
root@3b927950034f:/# passwd adriano
Enter new UNIX password:
Retype new UNIX password:
passwd: password updated successfully
...
```

Unfortunately, when the container dies the upper writeable layer is removed and all its content is lost unless a new image is created while the container is living. When a new image is created from a running container, only the changes made to the writeable layer, are added into the new layer.

To create a new layer from a running container
```
[root@host ~]# docker commit -m "added a new user" ubuntu ubuntu:latest
sha256:e46141824bfc8118d6f960b9be1d70bb917e2b159734ee2d2d26e2336521528a

[root@host ~]# docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
ubuntu              latest              e46141824bfc        2 minutes ago       132 MB
ubuntu              15.04               d1b55fd07600        14 months ago       131 MB


[root@host ~]# docker history ubuntu:latest
IMAGE               CREATED             CREATED BY                                      SIZE      COMMENT
e46141824bfc        40 seconds ago      /bin/bash                                       330 kB    added a new user
d1b55fd07600        14 months ago       /bin/sh -c #(nop) CMD ["/bin/bash"]             0 B
<missing>           14 months ago       /bin/sh -c sed -i 's/^#\s*\(deb.*universe\...   1.88 kB
<missing>           14 months ago       /bin/sh -c echo '#!/bin/sh' > /usr/sbin/po...   701 B
<missing>           14 months ago       /bin/sh -c #(nop) ADD file:3f4708cf445dc1b...   131 MB
```

Notice the new changed ubuntu image does not have its own copies of every layer. The new image is sharing its underlying layers with the previous image as following

![](../img/saving-space.jpg?raw=true)

All containers started from the latest image will share layers with all containers started from the first image. This will lead to optimize both image space usage and system performances.

## Persistent Volumes
Containers often require persistent storage for using, capturing, or saving data beyond the container life cycle. Utilizing persistent volume storage is required to keep data persistence. As a best practice, it is recommended to isolate the data from a containers, i.e. data management should be distinctly separate from the container life cycle.

Persistent storage is an important use case, especially for things like databases, images, file and folder sharing among containers. To achieve this goal, there are two different approaches:

  1. host based volumes
  2. shared hosts volumes

In the first case, persisten volumes reside on the same host where container is running. In the latter, volumes reside on a shared filesystem like NFS, GlusterFS or others. In the first case, data are persistent to the host, meaning if the orchestrator moves the container on another host, the content of the volume is no more accessible to the new container. In case of shared multi host storage, it takes advantage of a distributed filesystem combined with the explicit storage technique. Since the mount point is available on all nodes, it can be leveraged to create a shared mount point among containers. 

Persistent volumes are mapped from volumes defined into Dockerfile to filesystem on the hos running the container. For example, the following Dockerfile defines a volume ``/var/log`` where the web app stores its access logs
```
# Create the image from the latest nodejs
# The image is stored on Docker Hub at docker.io/kalise/nodejs-web-app:latest

FROM node:latest

MAINTAINER kalise <https://github.com/kalise/>

# Create app directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Install app dependencies
COPY package.json /usr/src/app/
RUN npm install

# Bundle app source
COPY . /usr/src/app

# Declare Env variables
ENV MESSAGE "Hello World!"

# Define the log mount point
VOLUME /var/log

# Expose the port server listen to
EXPOSE 8080
CMD [ "npm", "start" ]
```

Start a container from the nodejs image creating the volume
```
[root@centos ~]# docker run --name=nodejs \
   -p 80:8080 -d \
   -e MESSAGE="Hello" \
   -v /var/log \
docker.io/kalise/nodejs-web-app:latest
```

To find where the volume is located on the host machine, inspect the container
```
[root@centos ~]# docker inspect nodejs
```

```json
...
"Mounts": [
      {
          "Name": "84894a09fe25f503cd0f2d3a30eaa00a08d72190a92e2568d395cea5a277c456",
          "Source": "/var/lib/docker/volumes/84894a09fe25f503cd0f2d3a30eaa00a08d72190a92e2568d395cea5a277c456/_data",
          "Destination": "/var/log",
          "Driver": "local",
          "Mode": "",
          "RW": true,
          "Propagation": ""
      } ]
...
```

Please, note that data volumes persist even if the container itself is deleted.
```
[root@centos ~]# docker rm -f nodejs

[root@centos ~]# ls -l /var/lib/docker/volumes/84894a09fe25f503cd0f2d3a30eaa00a08d72190a92e2568d395cea5a277c456/
total 4
drwxr-xr-x 4 root root 4096 Apr 11 16:32 _data
```

Also they can be shared among different containers. Persistent volumes can be mounted on any point of the host file system. This helps sharing data between containers and host itself. For example, we can mount the volume above under the ``/logs`` directory of the host running the container

```
[root@centos ~]# docker run --name=nodejs \
   -p 80:8080 -d \
   -e MESSAGE="Hello" \
   -v /logs:/var/log \
docker.io/kalise/nodejs-web-app:latest
```

Volume data now are placed on the ``/logs`` directory
```
[root@centos ~]#  tailf /log/requests.log
1491922136506 ::ffff:10.10.10.1
1491922154632 ::ffff:10.10.10.1
...
```

The same volume could be mounted by another container, for example a container performing some analytics on the logs produced by the nodejs application. However, multiple containers writing to a single shared volume can cause data corruption. Make sure the application is designed to write to shared data stores.

### Wordpress example 
To demonstrate the use of persistent volumes we are going to setup a worpress application made of two containers:

    * The worpress PHP application
    * The MySQL MariaDB database

Both these containers will share some volumes for shared and persisten data.

The wordpress application is built via docker compose starting from the following ``docker-compose.yaml`` file
```yaml
version: '2'
services:
  mariadb:
    image: bitnami/mariadb:latest
    environment:
      MARIADB_ROOT_PASSWORD: bitnami123
      MARIADB_DATABASE: workpress
      MARIADB_USER: bitnami
      MARIADB_PASSWORD: bitnami123
    volumes:
      - mariadb_data:/bitnami/mariadb
  wordpress:
    image: bitnami/wordpress:latest
    environment:
      WORDPRESS_DATABASE_NAME: workpress
      WORDPRESS_DATABASE_USER: bitnami
      WORDPRESS_DATABASE_PASSWORD: bitnami123
    depends_on:
      - mariadb
    ports:
      - '80:80'
      - '443:443'
    volumes:
      - wordpress_data:/bitnami/wordpress
      - apache_data:/bitnami/apache
      - php_data:/bitnami/php

volumes:
  mariadb_data:
    driver: local
  wordpress_data:
    driver: local
  apache_data:
    driver: local
  php_data:
    driver: local
```

Create the application stack
```
[root@centos ~]# docker-compose up -d

Creating network "root_default" with the default driver
Creating volume "root_php_data" with local driver
Creating volume "root_apache_data" with local driver
Creating volume "root_wordpress_data" with local driver
Creating volume "root_mariadb_data" with local driver
Creating root_mariadb_1
Creating root_wordpress_1
```

Here the volumes
```
[root@centos ~]# ls -l /var/lib/docker/volumes/
...
-rw------- 1 root root 65536 Apr 11 17:01 metadata.db
drwxr-xr-x 3 root root    18 Apr 11 17:01 root_apache_data
drwxr-xr-x 3 root root    18 Apr 11 17:01 root_mariadb_data
drwxr-xr-x 3 root root    18 Apr 11 17:01 root_php_data
drwxr-xr-x 3 root root    18 Apr 11 17:01 root_wordpress_data
```

These volumes store persistent data like the MySQL database and will survive to containers.

## Registry
A Docker registry service is a storage and content delivery system containing tagged images. Main registry service is the official Docker Hub but users can build their own registry. Users interact with a registry by using push and pull commands.

```
[root@centos ~]# docker pull ubuntu:latest
```

The above command instructs the docker engine to pull the latest ubuntu image from the official Docker Hub. This is simply a shortcut for the longer
```
[root@centos ~]# docker pull docker.io/library/ubuntu:latest
```

To pull images from a local registry service, use
```
[root@centos ~]# docker pull <myregistrydomain>:<port>/kalise/ubuntu:latest
```

The above command instructs Docker Engine to contact the registry located at ``<myregistrydomain>:<port>`` to find the image ``kalise/ubuntu:latest``

In a typical deployment workflow, a commit to source code would trigger a build on Continous Integration system, which would then push a new image to the registry service. A notification from the registry triggers a deployment on a staging environment, or notify other systems that a new image is available.

### Deploy a local Registry Service
To deploy a local registry service on ``myregistry.example.com:5000``, install Docker on that server and then start a Registry container based on the standard registry image from Docker Hub
```
[root@centos ~]# docker pull registry:2
[root@centos ~]# docker run -d -p 5000:5000 --restart=always --name docker-registry registry:2
```

Get an image from the public Docker Hub, tag it to the local registry service
```
[root@centos ~]# docker pull docker.io/kalise/httpd
[root@centos ~]# docker tag docker.io/kalise/httpd myregistry.example.com:5000/kalise/httpd
```

The plain registry above is considered as insecure by Docker Engines. To make it accessible, each Docker Engine host should be instructed via systemd to trust the insecure registry service running on ``myregistry.example.com:5000`` host.

If the systemd uses the envinronment files
```
[root@centos ~]# systemctl show docker | grep EnvironmentFile
EnvironmentFile=/etc/sysconfig/docker (ignore_errors=yes)
EnvironmentFile=/etc/sysconfig/docker-storage (ignore_errors=yes)
EnvironmentFile=/etc/sysconfig/docker-network (ignore_errors=yes)

[root@centos ~]# vi /etc/sysconfig/docker
...
# If you have a registry secured with https but do not have proper certs
# distributed, you can tell docker to not look for full authorization by
# adding the registry to the INSECURE_REGISTRY line and uncommenting it.
# INSECURE_REGISTRY='--insecure-registry'
INSECURE_REGISTRY='--insecure-registry myregistry.example.com:5000'
...

[root@centos ~]# systemctl restart docker
```

Now the Docker Engine is trusting the local registry, so we can push images on it

```
[root@centos ~]# docker push myregistry.example.com:5000/kalise/httpd
[root@centos ~]# docker images
REPOSITORY                    TAG                 IMAGE ID            CREATED             VIRTUAL SIZE
myregistry.example.com:5000/kalise/httpd   latest              3de6516c8225        13 days ago         246.8 MB
docker.io/kalise/httpd        latest              3de6516c8225        13 days ago         246.8 MB
docker.io/registry            2                   ab0e69828861        2 weeks ago         171.2 MB
```

The image can be now pulled from the local registry
```
[root@centos ~]# docker pull myregistry.example.com:5000/kalise/httpd
```

To secure the registry with a self-signed certificate, first create the certificate
```
[root@centos ~]# mkdir /etc/certs
[root@centos ~]# cd /etc/certs
[root@centos ~]# openssl req \
-newkey rsa:4096 -nodes -sha256 -keyout domain.key \
-x509 -days 365 -out domain.crt
```

Then each Docker Engine host needs to be instructed to trust this certificate. 
```
[root@centos ~]# mkdir -p /etc/docker/certs.d/myregistry.example.com:5000
[root@centos ~]# cp /etc/certs/domain.crt /etc/docker/certs.d/myregistry.example.com:5000/ca.crt
```

Remove the insecure registry set in the previous step
```
[root@centos ~]# docker rm -f docker-registry
[root@centos ~]# vi /etc/sysconfig/docker
...
# If you have a registry secured with https but do not have proper certs
# distributed, you can tell docker to not look for full authorization by
# adding the registry to the INSECURE_REGISTRY line and uncommenting it.
# INSECURE_REGISTRY='--insecure-registry'
# INSECURE_REGISTRY='--insecure-registry myregistry.example.com:5000'
...
```

and restart the Docker Engine
```
[root@centos ~]# systemctl restart docker
```

Start the registry in secure mode passing the certificate as local volume and setting the related envinronment variables to the container
```
[root@centos ~]# docker run -d -p 5000:5000 --restart=always --name docker-registry \
  -v /etc/certs:/certs \
  -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/domain.crt \
  -e REGISTRY_HTTP_TLS_KEY=/certs/domain.key \
  registry:2
```

Now we can push/pull images to/from the local registry
```
[root@centos ~]# docker push myregistry.example.com:5000/kalise/httpd
[root@centos ~]# docker pull myregistry.example.com:5000/kalise/httpd
```

### Storage backend for registry
By default, data in containers is ephemeral, meaning it will disappears when the container registry dies. To make images a persistent data of the registry container, use a docker volume on the host filesystem.
```
[root@centos ~]# mkdir /data
[root@centos ~]# docker run -d -p 443:5000 --restart=always --name docker-registry \
-v /data:/var/lib/registry \
-v /etc/certs:/certs \
-e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/domain.crt \
-e REGISTRY_HTTP_TLS_KEY=/certs/domain.key \
registry:2

[root@centos ~]# docker pull docker.io/httpd:latest
[root@centos ~]# docker tag docker.io/httpd myregistry.example.com/httpd
[root@centos ~]# docker push myregistry.example.com/httpd
[root@centos ~]# docker run -d -p 8080:80 myregistry.example.com/httpd
```

Having used local file system directory ``/data`` as backend for the registry container, images pushed on that registry will survive to registry crashes or dies. However, having used a persistent backend does not prevent data loss due to local storage fails. For production use, a safer option is using a shared storage like NFS share.

On a remote NFS server, configure the path ``/exports/registry`` as NFS share
```
[root@centos ~]# mkdir -p /exports/registry
[root@centos ~]# yum install -y nfs-utils
[root@centos ~]# chown nfsnobody:nfsnobody /exports/registry
[root@centos ~]# chmod 777 /exports/registry
[root@centos ~]# vi /etc/exports
/exports/registry *(rw,sync,all_squash)

[root@centos ~]# systemctl enable rpcbind nfs-server
[root@centos ~]# systemctl start rpcbind nfs-server nfs-lock nfs-idmap
```

Note that the volume is owned by nfsnobody and access by all remote users is squashed to be access by this user. This essentially disables user permissions for clients mounting the volume.


On the machine hosting the Registry service
```
[root@centos ~]# yum install -y nfs-utils
[root@centos ~]# mkdir /mnt/registry
[root@centos ~]# mount <IP_NFS_SERVER>:/exports/registry /mnt/registry
[root@centos ~]# docker run -d -p 443:5000 --restart=always --name docker-registry \
-v /mnt/registry:/var/lib/registry \
-v /etc/certs:/certs \
-e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/domain.crt \
-e REGISTRY_HTTP_TLS_KEY=/certs/domain.key \
registry:2
```

Make sure the shared path ``<IP_NFS_SERVER>:/exports/registry`` is mounted at startup by editing the ``/etc/fstab`` file. Now the registry service is backed by a NFS for protection from container exits and local disk failures.

### Registry Configuration Reference
More options are available on registry configuration. The Registry configuration is based on a YAML file located at path ``/etc/docker/registry/config.yml`` of the registry container.
```
[root@centos ~]# docker exec -it registry bash
root@c92c03d2d2eb:/#
root@c92c03d2d2eb:/# cat /etc/docker/registry/config.yml
version: 0.1
log:
  fields:
    service: registry
storage:
    cache:
        blobdescriptor: inmemory
    filesystem:
        rootdirectory: /var/lib/registry
http:
    addr: :5000
    headers:
        X-Content-Type-Options: [nosniff]
health:
  storagedriver:
    enabled: true
    interval: 10s
    threshold: 3
```
