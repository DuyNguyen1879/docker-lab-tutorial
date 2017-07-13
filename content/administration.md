# Admin the Docker Engine
In this section, we are going to see basic admin tasks about the Docker Engine. As reference in this tutorial, we are using CentOS 7 Operating System. Tasks can behave different on other systems.

  * [Configure the engine](#configure-the-engine)
  * [Securing the engine with TLS](#securing-the-engine-with-tls)
  * [Accessing the engine with APIs](#accessing-the-engine-with-apis)
  
## Configure the engine
After successfully installing and starting docker, the dockerd daemon runs with its default configuration. On CentOS systems, the docker engine is managed via systemd

    systemctl status docker
  
Before starting docker, configure it in case of running it with different configuration settings. For example, on CentOS systems, the preferred storage driver is the devicemapper instead of the overlay (default value). The recommended way from Docker web site is to use the platform-independent ``/etc/docker/daemon.json`` file instead of the systemd unit file. This file is available on all the Linux distributions.

```json
{
 "debug": true,
 "storage-driver": "devicemapper",
}
```

After configuring the engine, start and enable it as system service

    systemctl start docker
    systemctl enable docker

## Securing the engine with TLS
