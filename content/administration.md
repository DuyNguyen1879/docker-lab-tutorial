# Admin the Docker Engine
In this section, we are going to see basic admin tasks about the Docker Engine. As reference in this tutorial, we are using CentOS 7 Operating System. Tasks can behave different on other systems.

  * [Configure the engine](#configure-the-engine)
  * [Securing the engine with TLS](#securing-the-engine-with-tls)
  * [Accessing the engine with APIs](#accessing-the-engine-with-apis)
  
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

## Securing the engine with TLS
By default docker engine has no authentication or authorization, relying instead on the filesystem security of its unix socket which by default is only accessible by the root user. For accessing docker engine via remote clients (both gui and cli), it is possible to secure it via TLS. To provide proof of identity, Docker supports TLS certificates both on the server and the client side. When set up correctly, it will only allow clients and servers with a certificate signed by a specific CA to talk to eachother.

On any Linux machine with OpenSSL installed, create a folder where store certificates and keys

    mkdir -p ./docker-pki
    cd ./docker-pki
    
The docker two-way authentication requires the server to have two certificates: the Certification Authority certificate and the server certificate and a private key. It also requires the client to have two certificates: the Certification Authority certificate and the client certificate and a private key:

![](../img/tls.png?raw=true)

The CA Server is not required in this tutorial since we are using a self generated Certificated Authority certificate.



### Create Certification Authority certificate and key
Create a **CA** private key file ``ca-key.pem`` with encryption

    openssl genrsa -aes256 -out ca-key.pem 4096

This is the private key used to 























