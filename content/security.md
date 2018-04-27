# Security
In this section, we'll walk through security topics for the docker engine.

  * [Securing the engine](#securing-the-engine)
  * [User Namespaces](#user-namespaces)

## Securing the engine
By default docker engine has no authentication or authorization, relying instead on the filesystem security of its unix socket which by default is only accessible by the root user. For accessing docker engine via remote clients (both gui and cli), it is possible to secure it via TLS. To provide proof of identity, Docker supports TLS certificates both on the server and the client side. When set up correctly, it will only allow clients and servers with a certificate signed by a specific **Certification Authority** to talk to each other.

The docker two-way authentication requires the server to have two certificates: the **Certification Authority** certificate and the server certificate and a private key. It also requires the client to have two certificates: the **Certification Authority** certificate and the client certificate and a private key:

![](../img/detls.png?raw=true)

Please, remember this is only an example: dealing with a real **Certificate Authority** will be slightly different.

### Install the required tools
On any Linux machine install OpenSSL, create a folder where store certificates and keys

    openssl version
    OpenSSL 1.0.1e-fips 11 Feb 2013
    
    mkdir -p ./docker-pki
    cd ./docker-pki
    
To speedup things, in this lab, we'll use the **CloudFlare** TLS toolkit for helping us in TLS certificates creation. Details on this tool and how to use it are [here](https://github.com/cloudflare/cfssl).

Install the tool

    wget https://pkg.cfssl.org/R1.2/cfssl_linux-amd64
    wget https://pkg.cfssl.org/R1.2/cfssljson_linux-amd64

    chmod +x cfssl_linux-amd64
    chmod +x cfssljson_linux-amd64

    mv cfssl_linux-amd64 /usr/local/bin/cfssl
    mv cfssljson_linux-amd64 /usr/local/bin/cfssljson

### Create Certification Authority certificate and key
The **Certification Authority** entity is not required in this lab since we are using a self generated **Certification Authority**. Create a **Certification Authority** configuration file ``ca-config.json`` as following

```json
{
  "signing": {
    "default": {
      "expiry": "8760h"
    },
    "profiles": {
      "custom": {
        "usages": ["signing", "key encipherment", "server auth", "client auth"],
        "expiry": "8760h"
      }
    }
  }
}
```

Create the configuration file ``ca-csr.json`` for the **Certification Authority** signing request

```json
{
  "CN": "NoverIT",
  "key": {
    "algo": "rsa",
    "size": 4096
  },
  "names": [
    {
      "C": "IT",
      "ST": "Italy",
      "L": "Milan",
      "O": "My Own Certification Authority"
    }
  ]
}
```

Generate a CA certificate and private key:

    cfssl gencert -initca ca-csr.json | cfssljson -bare ca

As sesult, we have following files

    ca-key.pem
    ca.pem

They are the key and the certificate of our self signed Certification Authority.

### Create certificate and key for the server
Create the configuration file ``server-csr.json`` for server certificate signing request

```json
{
  "CN": "docker-engine",
  "hosts": [
    "docker",
    "10.10.10.60",
    "127.0.0.1",
    "localhost"
  ],
  "key": {
    "algo": "rsa",
    "size": 4096
  }
}
```

If you have a cluster of docker engines, e.g. a Swarm cluster, make sure to add all the docker engine addresses and hostnames. This avoids us to create a separate pair of key/certificate for each engine in the cluster.

Create the key pair

    cfssl gencert \
       -ca=ca.pem \
       -ca-key=ca-key.pem \
       -config=ca-config.json \
       -profile=custom \
       server-csr.json | cfssljson -bare server

This will produce the ``server.pem`` certificate file containing the public key and the ``server-key.pem`` file, containing the private key. Move the server's keys pair as well as the ``ca.pem`` file to a given location on the docker server, e.g.``/etc/docker/ssl`` where the docker engine is running
    
      scp ca.pem docker:/etc/docker/ssl/ca.pem
      scp server.pem docker:/etc/docker/ssl/server-cert.pem
      scp server-key.pem docker:/etc/docker/ssl/server-key.pem

We'll instruct the docker engine to use these files. To improve secutity, make sure the private key file will be safe, e.g. changing the file permissions.

### Create certificate and key for the client
Since TLS authentication in docker is a two way authentication between client and server, we need to create a client's keys pair. Create the ``client-csr.json`` configuration file for the docker client.

```json
{
  "CN": "docker-client",
  "hosts": [
    "127.0.0.1",
    "localhost"
  ],
  "key": {
    "algo": "rsa",
    "size": 4096
  }
}
```

Create the key pair

    cfssl gencert \
       -ca=ca.pem \
       -ca-key=ca-key.pem \
       -config=ca-config.json \
       -profile=custom \
       client-csr.json | cfssljson -bare client

Once we have the private key ``client-key.pem``, and the client certificate ``client.pem``, we can proceed to secure the docker client. Move the client's keys pair as well as the ``ca.pem`` file to a given location, e.g. ``$HOME/.docker`` on the client used to connect the docker engine
    
    cp ca.pem $HOME/.docker/ca.pem
    cp client.pem $HOME/.docker/cert.pem
    cp client-key.pem $HOME/.docker/key.pem

We'll instruct the docker client to use these files. To improve secutity, make sure the private key file will be safe, e.g. changing the file permissions.

After generating the server and client certificates, we can safely remove the certificate signing requests files

    rm -rf *.csr

### Enable TLS verification
On the server, stop the docker engine and edit the docker daemon ``/etc/docker/daemon.json`` configuration file as following
```json
{
 "debug": true,
 "storage-driver": "devicemapper",
 "tls": true,
 "tlscacert": "/etc/docker/ssl/ca.pem",
 "tlscert": "/etc/docker/ssl/server-cert.pem",
 "tlskey": "/etc/docker/ssl/server-key.pem",
 "hosts": ["tcp://0.0.0.0:2376","unix:///var/run/docker.sock"]
}
```

Restart the engine and check the engine is listening on the secure port 

    netstat -natp | grep -i 2376
    
    Proto Recv-Q Send-Q Local Address Foreign Address   State   PID/Program name
    tcp6       0      0 :::2376       :::*              LISTEN  15803/dockerd

On the client, force the TLS by setting the options

    docker --tlsverify \
           --tlscacert=$HOME/.docker/ca.pem \
           --tlscert=$HOME/.docker/cert.pem \
           --tlskey=$HOME/.docker/key.pem \
           --host=docker-engine:2376 version

To secure client by default, without adding tls and host info for every call to the engine, export the following environment variables in a bash profile ``docker-tls.rc`` file

```bash
export PS1='[\W(tls)]\$ '
export DOCKER_HOST=tcp://docker-engine:2376
export DOCKER_TLS_VERIFY=1
export DOCKER_CERT_PATH=$HOME/.docker  # {ca,cert,key}.pem directory
```

Then source the file and connect the server

    source docker-tls.rc
    [~(tls)]# docker version

## User Namespaces
In Linux, namespaces are essential to the functioning of containers as we know them. The user namespace is a tecnique to maps the UIDs and GIDs inside a container to the regular users and group in the host system.

### Container root user
For example, the PID namespace is what keeps processes in one container from seeing or interacting with processes in another container or, in the host system. A process might have the apparent ``PID=1`` inside a container

    [root@centos ~]# docker run -it --rm ubuntu:latest /bin/bash
    root@f1ad1406edd4:/# ps -ef
    UID        PID  PPID  C STIME TTY          TIME CMD
    root         1     0  0 12:47 ?        00:00:00 /bin/bash
    root        11     1  0 12:51 ?        00:00:00 ps -ef

the process will have an ordinary PID on the host system.

    [root@centos ~]# ps -ef | grep bash
    UID        PID  PPID  C STIME TTY          TIME CMD
    ...
    root     23316 23305  0 14:47 pts/3    00:00:00 /bin/bash
    root     23354 12429  0 14:53 pts/2    00:00:00 grep --color=auto bash

The PID namespace is responsible for remapping PIDs inside the container. However, in the example above, we see the root user inside the container to be mapped with the root user on the host system. Even the rrot user in container cannot go wild on the host, this could be security hole.

A way to avoid this pitfail is to run processes in container as no-root user. This is accomplished by the ``USER`` directive in Dockerfile. For example the following create a container for running python apps as no-root user

    FROM centos:latest
    RUN yum update -y && yum install -y sudo && yum clean all
    RUN groupadd -r kalise -g 1969 && \
        useradd -u 1969 -r -g kalise -m -d /app -s /sbin/nologin kalise && \
        chmod 755 /app
    RUN echo "kalise ALL=(root) NOPASSWD:ALL" > /etc/sudoers.d/kalise && \
        chmod 0440 /etc/sudoers.d/kalise
    WORKDIR /app
    USER kalise
    CMD ["python", "-m", "SimpleHTTPServer"]

The container started from the above will run the python ``SimpleHTTPServer`` application as no-root user kalise with ``UID=1969`` and ``GID=1969``

Compile the image above and start a container

    docker build -t httpd:latest ./Dockerfile
    docker run --rm --name simple httpd:latest

On the host machine

    [root@centos ~]# ps -ef | grep python
    UID        PID  PPID  C STIME TTY          TIME CMD
    1969     28563 28550  0 16:09 ?        00:00:00 python -m SimpleHTTPServer
    root     28585 12429  0 16:10 pts/2    00:00:00 grep --color=auto python

Inside the container

    [root@centos ~]# docker exec -it simple /bin/bash
    [kalise@270009b0d141 ~]$ ps -ef
    UID        PID  PPID  C STIME TTY          TIME CMD
    kalise       1     0  0 14:09 ?        00:00:00 python -m SimpleHTTPServer
    kalise       5     0  0 14:12 ?        00:00:00 /bin/bash
    kalise      20     5  0 14:12 ?        00:00:00 ps -ef
    [kalise@270009b0d141 ~]$

This could prevent the user kalise to get any priviledges into the host machine. However, for containers whose processes must run as the root user within the container, we can re-map this user to a less-privileged user on the host. The mapped user is assigned a range of UIDs which function within the container as normal user but have no privileges on the host itself. 

### Configure User Namespace
To use the user namespace, it should be configured and enabled on the Docker engine. It effects all containersOn the host machine, however it can be electively disabled per container.

Stop the docker daemon and edit the configuration file ``/etc/docker/daemon.json`` as following

    {
     "debug": true,
     "userns-remap": "dummy"
    }

where ``dummy`` is the user on the host whom the root users into containers will be mapped.

Before to restart the engine, we need to set up the host for using user namespaces. On CentOS machine, check the kernel running version, enable the user namespace, and restart the machine 

    kernel=$(uname -r)
    grubby --args="user_namespace.enable=1" --update-kernel=/boot/vmlinuz-$kernel
    init 6

On reboot, configure the dummy user. It doesn't necessarily need to be a fullly-fledged user

    adduser -r -s /bin/nologin dummy

We also need to have subordinate UID and GID ranges specified in the ``/etc/subuid`` and ``/etc/subgid`` files

    echo dummy:100000:65536 > /etc/subuid
    echo dummy:100000:65536 > /etc/subgid

In the example above, ``100000`` represents the first UID in the range of available UIDs that processes within the container may run with; ``65536`` represents the maximum number of UIDs that may be used by a container. If a process within the container is running as with ``UID=1``, on the host system it would run with the ``UID=100000``.

Now restart the docker engine. **Note:** *when enabling the user namesapces, the docker engine hide all phe previous objects like containers, images, volumes, networks, etc. This is because the remapped engine operates in a new environment. Every remapping will get its own directory ``/var/lib/docker/xxx.yyy`` format xxx is the subordinate UID and yyy is the subordinate GID.

Let's to see how a remapped engine works.

Create a new container

    [root@centos ~]# docker run -it --rm ubuntu:latest /bin/bash
    root@33ba8fc8c4f5:/# ps -ef
    UID        PID  PPID  C STIME TTY          TIME CMD
    root         1     0  0 16:18 ?        00:00:00 /bin/bash
    root         9     1  0 16:19 ?        00:00:00 ps -ef
    root@33ba8fc8c4f5:/#

On the host machine

    [root@centos]# ps -ef | grep bash
    ...
    UID        PID  PPID  C STIME TTY          TIME CMD
    100000    2978  2966  0 18:18 pts/3    00:00:00 /bin/bash
    root      3012  2527  0 18:23 pts/1    00:00:00 grep --color=auto bash

We see the process ``UID=1`` in container is running as root but that process is mapped back to the dummy user on the host with ``UID=100000``. 

The user namespaces feature, can be selectively disabled per container by starting the single container with the ``--userns=host`` option

        [root@centos ~]# docker run -it --rm --userns=host ubuntu:latest /bin/bash
        
        root@99ed855c0383:/# top &
        [1] 11
        
        root@99ed855c0383:/# ps -ef
        UID        PID  PPID  C STIME TTY          TIME CMD
        root         1     0  0 16:30 ?        00:00:00 /bin/bash
        root        11     1  0 16:32 ?        00:00:00 top
        root        13     1  0 16:32 ?        00:00:00 ps -ef


On the host machine

        [root@centos ~]# ps -ef | grep top
        UID        PID  PPID  C STIME TTY          TIME CMD
        ...
        root      3247  3218  0 18:32 pts/4    00:00:00 top
        root      3252  2572  0 18:33 pts/2    00:00:00 grep --color=auto top

we see the user root in the container to be mapped on the user root.

To disable the feature, stop the engine, remove the ``"userns-remap": "dummy"`` from the ``/etc/docker/daemon.json`` file and restart the engine.
