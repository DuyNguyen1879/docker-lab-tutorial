# Administration tasks
In this section, we are going to see basic admin tasks about the docker engine and the swarm cluster. As reference in this tutorial, we are using CentOS 7 Operating System. Tasks can be different on other systems.

  * [Configure the engine](#configure-the-engine)
  * [Securing the engine](#securing-the-engine)
  * [Securing the cluster](#securing-the-cluster)
  * [Docker APIs](#docker-apis)
  
## Configure the engine
After successfully installing and starting docker, the dockerd daemon runs with its default configuration. On CentOS systems, the docker engine is managed via systemd

    systemctl status docker
  
Before starting docker, configure it in case of running it with different configuration settings. For example, on CentOS systems, the preferred storage driver is the devicemapper instead of the overlay (default value). The recommended way from Docker web site is to use the platform-independent ``/etc/docker/daemon.json`` file instead of the systemd unit file.

On CentOS systems, the basic configuration file could be as following
```json
{
 "debug": false,
 "storage-driver": "devicemapper",
}
```

After configuring the engine, start and enable it as system service

    systemctl start docker
    systemctl enable docker

The docker engine, by default, is listening for client connections on the ``/var/run/docker.sock`` unix socket. To make it listening also on a TCP socket, configure it as following:
```json
{
 "debug": false,
 "storage-driver": "devicemapper",
 "hosts": ["tcp://0.0.0.0:2375","unix:///var/run/docker.sock"]
}
```

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
Create the configuration file ``sserver-csr.json`` for server certificate signing request

```json
{
  "CN": "docker-engine",
  "hosts": [
    "swarm00",
    "swarm00",
    "swarm00",
    "swarm00",
    "swarm00",
    "10.10.10.60",
    "10.10.10.61",
    "10.10.10.62",
    "10.10.10.63",
    "10.10.10.64",
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

This will produce the ``server.pem`` certificate file containing the public key and the ``server-key.pem`` file, containing the private key. Move the server's keys pair as well as the ``ca.pem`` file to a given location on server, e.g.``/etc/docker/ssl`` where the docker engine is running
    
    for host in swarm00 swarm01 swarm02 swarm03 swarm04; do
      scp ca.pem ${host}:/etc/docker/ssl/ca.pem
      scp server.pem ${host}:/etc/docker/ssl/server-cert.pem
      scp server-key.pem ${host}:/etc/docker/ssl/server-key.pem
    done

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


## Securing the cluster
By default, the swarm cluster is encrypted with AES-GCM. Authentication between nodes partecipating into the cluster is done with mutual TLS.

When you create a swarm the docker node designates itself as a manager node. By default, the manager node generates a new Certificate Authority (CA) along with a key pair, made of public key ``swarm-node.crt`` and a private key ``swarm-node.key``, which are used to secure communications with other nodes joining the swarm. The certificates is rotated every 90 days.

Certificates and keys are under ``/var/lib/docker/swarm/certificates/`` directory 

    ll /var/lib/docker/swarm/certificates/
    
    -rw-r--r-- 1 root root 1376 Jul 14 19:00 swarm-node.crt
    -rw------- 1 root root  302 Jul 14 19:00 swarm-node.key
    -rw-r--r-- 1 root root  550 Jul 14 19:00 swarm-root-ca.crt

Each time a new node joins the swarm, the manager issues a certificate to that node. The certificate contains a randomly generated node ID to identify the node under the certificate common name (CN) and the role under the organizational unit (OU). The node ID serves as secure node identity for the lifetime of the node in the current swarm.

The manager node also generates two tokens to use when you join additional nodes to the swarm: one worker token and one manager token. Each token includes the digest of the root CA’s certificate and a randomly generated secret.

To generate a manager token
```
[root@swarm00 ~]# docker swarm join-token manager
To add a manager to this swarm, run the following command:

    docker swarm join \
    --token SWMTKN-1-0a1z3yz75jsin2rf5az5y6ylk8uihdwdb7nmxz0uvc9icnmbg2-dewdemfe3da4dq8aj18a7jnce \
    192.168.2.60:2377
```

For a worker token
```
[root@swarm00 ~]# docker swarm join-token worker
To add a worker to this swarm, run the following command:

    docker swarm join \
    --token SWMTKN-1-0a1z3yz75jsin2rf5az5y6ylk8uihdwdb7nmxz0uvc9icnmbg2-1ij50ku39k2q5nn0gmr5x6f6j \
    192.168.2.60:2377
```

When a new node joins the swarm, the joining node uses the digest to validate the root CA certificate from the remote manager. The remote manager uses the secret to ensure the joining node is an approved node.

## Docker APIs
The docker engine provide a complete set of REST APIs.

For example

    curl  http://docker-engine:2375/version | jq .

returns

```json
{
  "Version": "17.06.0-ce",
  "ApiVersion": "1.30",
  "MinAPIVersion": "1.12",
  "GitCommit": "02c1d87",
  "GoVersion": "go1.8.3",
  "Os": "linux",
  "Arch": "amd64",
  "KernelVersion": "3.10.0-514.26.2.el7.x86_64",
  "BuildTime": "2017-06-23T21:21:56.086156633+00:00"
}
```

With the Python SDK, create ``docker-version.py`` script 
```python
#!/usr/bin/python
# https://github.com/kalise
# Usage: <command> -h host -p port
# -h, --host host to connect
# -p, --port port to connect, default is 2375

import sys, getopt, os
import docker

def main(argv):
  host = "localhost"
  port = "2375"
  options, remaining = getopt.getopt(sys.argv[1:], 'h:p', ['host=','port='])
  print "ARGV      :", sys.argv
  print "OPTIONS   :", options
  print "REMAINING :", remaining
  for opt, arg in options:
      if opt in ('-h','--host'):
          host = arg
      elif opt in ('-p','--port'):
          port = arg

  base_url = "tcp://" + host + ":" + port
  print "HOST      :", base_url
  client = docker.DockerClient(base_url)
  version = client.version()
  print "VERSION   :", version["Version"]

if __name__ == "__main__":
  main(sys.argv[1:])
```

call the script against the server

```bash
python docker-version.py -h docker-engine -p 2375

ARGV      : ['./docker-version', '-h', 'docker-engine', '-p', '2375']
OPTIONS   : [('-h', 'docker-engine'), ('-p', '2375')]
REMAINING : []
HOST      : tcp://docker-engine:2375
VERSION   : 17.03.2-ee-4
```
