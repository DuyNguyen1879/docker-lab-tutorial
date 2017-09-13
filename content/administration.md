# Administration tasks
In this section, we are going to see basic admin tasks about the docker engine and the swarm cluster. As reference in this tutorial, we are using CentOS 7 Operating System. Tasks can be different on other systems.

  * [Configure the engine](#configure-the-engine)
  * [Docker APIs](#docker-apis)
  
## Configure the engine
After successfully installing and starting docker, the dockerd daemon runs with its default configuration. On CentOS systems, the docker engine is managed via systemd

    systemctl status docker
  
Before starting docker, configure it in case of running it with different configuration settings. For example, on CentOS systems, the preferred storage driver is the devicemapper instead of the overlay (default value). The recommended way from Docker web site is to use the platform-independent ``/etc/docker/daemon.json`` file instead of the systemd unit file.

On CentOS systems, the basic configuration file could be as following
```json
{
 "debug": false,
 "storage-driver": "devicemapper"
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
