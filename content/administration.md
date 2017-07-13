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

    openssl version
    OpenSSL 1.0.1e-fips 11 Feb 2013
    
    mkdir -p ./docker-pki
    cd ./docker-pki
    
The docker two-way authentication requires the server to have two certificates: the Certification Authority certificate and the server certificate and a private key. It also requires the client to have two certificates: the Certification Authority certificate and the client certificate and a private key:

![](../img/tls.png?raw=true)

Please, remember this is only an example: dealing with a real Certificate Authority will be slightly different.

### Create Certification Authority certificate and key
The CA Server is not required in this tutorial since we are using a self generated Certificated Authority. Create a **CA** key file ``ca-key.pem`` with an encrypted passphrase

    openssl genrsa -aes256 -out ca-key.pem 4096

This is the key used to sign client and server certificates against the Certification Authority. It is NOT the private key used in the client/server communication. We'll create these keys later. To inspect the just created key, use the ``openssl rsa -in ca-key.pem -text`` command. If you are interested in to extract the public part from this key, use the command ``openssl rsa -in ca-key.pem -pubout``.

Now create the CA certificate ``ca.pem`` file using the key above

    openssl req -new -x509 -days 3650 -key ca-key.pem -sha256 -out ca.pem

This is an interactive process, asking for information about the Certificate Authority. Since we're creating our own Certification Authority, no too much constraints here.

Inspect the certificate

    openssl x509 -in ca.pem -noout -text
    
    Certificate:
        Data:
            Version: 3 (0x2)
            Serial Number: 15209141164087594974 (0xd311b94ea8364fde)
        Signature Algorithm: sha256WithRSAEncryption
            Issuer: C=IT, ST=Italy, L=Milan, O=NoverIT, CN=kalise
            Validity
                Not Before: Jul 13 18:06:54 2017 GMT
                Not After : Jul 11 18:06:54 2027 GMT
            Subject: C=IT, ST=Italy, L=Milan, O=NoverIT, CN=kalise
            Subject Public Key Info:
                Public Key Algorithm: rsaEncryption
                    Public-Key: (4096 bit)

As convenience, we set the validity of this certificate as for 10 years.

### Create certificate and key for the server
Create the private key ``server-key.pem`` file for the docker engine server

    openssl genrsa -out server-key.pem 4096

Once we have a private key, we can proceed to create a Certificate Signing Request (**CSR**). This is a formal request asking the CA to sign a certificate. The request contains the public key of the entity requesting the certificate and some information about the entity. This data will be part of the certificate.

Create the request

    HOST=docker-engine
    openssl req -subj "/CN=$HOST" -sha256 -new -key server-key.pem -out server.csr

Make sure that Common Name (**CN**) matches the hostname of the docker engine.

Sign the certificate

    openssl x509 -req -days 3650 -sha256 -in server.csr \
                 -CA ca.pem \
                 -CAkey ca-key.pem \
                 -CAcreateserial -out server-cert.pem

This will produce the ``server-cert.pem`` certificate file containing the public key to authenticate against the server running the docker engine. Together with the ``server-key.pem`` file, this makes up a server's keys pair.

Move the server's keys pair as well as the ``ca.pem`` file to a given location on server where the docker engine is running

    mkdir -p /etc/docker/ssl/
    mv ca.pem /etc/docker/ssl/ca.pem
    mv server-cert.pem /etc/docker/ssl/server-cert.pem
    mv server-key.pem /etc/docker/ssl/server-key.pem

We'll instruct the docker engine to use these files. To improve secutity, make sure the private key file will be safe, e.g. changing the file permissions.

#### Creating Certificates Valid for Multiple Hostnames
By default, certificates have only one Common Name (**CN**) and are valid for only one hostname. Because of this, having a cluster of docker engines, we are forced to use a separate certificate for each node. In this situation, using a single multidomain certificate makes much more sense. For this example, create an estention file ``openssl.cnf`` with the following content

    subjectAltName = @alt_names

    [alt_names]
    DNS.0 = swarm00
    IP.0 = 10.10.10.60
    DNS.1 = swarm01
    IP.1 = 10.10.10.61
    DNS.2 = swarm02
    IP.2 = 10.10.10.62
    DNS = localhost
    IP = 127.0.0.1

Sign the certificate

    openssl x509 -req -days 3650 -sha256 -in server.csr \
                 -CA ca.pem \
                 -CAkey ca-key.pem \
                 -CAcreateserial -out server-cert.pem \
                 -extfile openssl.cnf

When a certificate contains alternative names, the Common Name is ignored. Newer certificates produced by CA may not even include any Common Names. For this reason, include all desired hostnames on the alternative names configuration file.

### Create certificate and key for the client
Since TLS authentication in docker is a two way authentication between client and server, we need to create a client's keys pair. Create the private key ``key.pem`` file for the docker client.

    openssl genrsa -out key.pem 4096

Once we have a private key, we can proceed to create a Certificate Signing Request for the client. For the client certificate, we can use an arbitrary name for the Common Name option.

    openssl req -subj '/CN=client' -new -key key.pem -out client.csr

To make the certificate suitable for client authentication, create an extensions configuration ``client.cnf`` file and sign the certificate

    echo extendedKeyUsage = clientAuth > client.cnf
    openssl x509 -req -days 365 -sha256 -in client.csr \
                 -CA ca.pem \
                 -CAkey ca-key.pem \
                 -CAcreateserial -out cert.pem \
                 -extfile client.cnf

This will produce the ``cert.pem`` certificate file containing the public key for the client. Together with the ``key.pem`` file, this makes up a client's keys pair.

Move the client's keys pair as well as the ``ca.pem`` file to a given location on the client used to connect the docker engine

    mkdir -p $HOME/.docker
    mv ca.pem $HOME/.docker/ca.pem
    mv cert.pem $HOME/.docker/cert.pem
    mv key.pem $HOME/.docker/key.pem

We'll instruct the docker client to use these files. To improve secutity, make sure the private key file will be safe, e.g. changing the file permissions.

After generating the server and client certificates, we can safely remove the two certificate signing requests as well as the extension configuration files

    rm -rf *.csr
    rm -rf *.cnf

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

To secure client by default, wwithout adding tls and host info for every call to the engine, export the following environment variables in a bash profile ``docker-tls.rc`` file

```bash
export PS1='[\W(tls)]\$ '
export DOCKER_HOST=tcp://docker-engine:2376
export DOCKER_TLS_VERIFY=1
export DOCKER_CERT_PATH=$HOME/.docker  # {ca,cert,key}.pem directory
```

Then source the file and connect the server

    source docker-tls.rc
    [~(tls)]# docker version


## Accessing the engine with APIs
The docker engine provide a complete set of REST APIs. The APIs can be accessed with any HTTP client, but it also provide Python and Go SDKs.

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
