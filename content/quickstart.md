# Start with containers
Docker allows to run applications inside Linux Containers.

  * [Running a container](#running-a-container)
  * [Working inside a container](#working-inside-a-container)
  * [Inspecting a container](#inspecting-a-container)

Docker provides a command line client to interact with Docker engine via restfull APIs. If you need to access the Docker engine remotely, you need to enable the engine to listen on tcp socket port 2375 for unsecure access and port 2376 for encrypted TLS access.
Beware that the default setup provides un-encrypted and un-authenticated direct access to the Docker daemon and should be secured either using the built in HTTPS encrypted socket, or by putting a secure web proxy in front of it.

## Running a container
Run an application by using the Docker client
```
# docker run busybox echo 'Hello Docker'
Hello Docker

# docker run busybox whoami
root

# docker run busybox route
Destination     Gateway         Genmask         Flags Metric Ref    Use Iface
default         172.17.0.1      0.0.0.0         UG    0      0        0 eth0
172.17.0.0      *               255.255.0.0     U     0      0        0 eth0
```

In the above examples, the format is ``docker run <image> <command>`` where ``busybox`` is the Busybox image to run and ``echo``, ``whoami``, ``route`` are the commands to run inside the container.

When the client specifies an image, Docker looks first for the image on local host. If the image does not exist locally, then the image is pulled from the public image registry Docker Hub.

Run the Busybox container interactively
```
# docker run -it busybox
/ # echo "Hello Docker"
Hello Docker
/ # exit
#
```
The ``-i`` option creates an interactive session and ``-t`` option opens a terminal session. Without ``-i``, the shell would open and then exit and without ``-t``, the shell would stay open, but it is impossible to type anything to the shell


Run a container in daemon mode on a random port
```
# docker run -d httpd
```

Run a container in daemon mode on a defined container port
```
# docker run -d -p 5000 httpd
```

Run a container in daemon mode and expose the container to a defined host port
```
# docker run -d -p 4000:80 httpd

# netstat -natp | grep 4000
tcp6       0      0 :::4000                 :::*                    LISTEN      15140/docker-proxy-

# curl localhost:4000
<html><body><h1>It works!</h1></body></html>
```

Expose all ports as defined in the container. All ports will be exposed to random ports
```
# docker run -d -P nginx
docker ps
CONTAINER ID  IMAGE   COMMAND      CREATED     STATUS        PORTS                NAMES
9bfe5c2b1769  nginx   "nginx -g"   4 minutes   Up 4 minutes  0.0.0.0:32769->80/tcp, 0.0.0.0:32768->443/tcp
```

Specify the container name
```
# docker run -d -p 4000:80 --name webserver httpd
```

List running containers
```
# docker ps
CONTAINER ID  IMAGE   COMMAND             CREATED         STATUS        PORTS                NAMES
f312f456b54f  httpd   "httpd-foreground"  10 seconds ago  Up 9 seconds  0.0.0.0:80->80/tcp   webserver
```

List all containers
```
# docker ps -a
CONTAINER ID  IMAGE     COMMAND             CREATED         STATUS        PORTS                NAMES
f312f456b54f  httpd     "httpd-foreground"  10 seconds ago  Up 9 seconds  0.0.0.0:80->80/tcp   webserver
027758d7be6b  wordpress "/app-entrypoint.sh n"   12 days ago          Exited (1) 6 days ago  wordpress
```

Control a container
```
# docker stop|start|restart webserver
```

Remove a stopped container
```
# docker rm webserver
```

Force remove a running container
```
# docker rm -f webserver
```

Remove all containers
```
docker rm `docker ps -aq`
```

Start a container and remove it when the container exits
```
# docker run --rm -it busybox
```

## Working inside a container
Once you run a container in interactive mode, you are presented with a shell prompt and you can start commands from inside the container. For example, let's to install the ``nmap`` tool inside a CentOS base image
```
# docker run -it --name centos_bash centos
[root@8de7b5e65c98 /]# nmap 8.8.8.8
bash: nmap: command not found
[root@8de7b5e65c98 /]# yum install -y nmap
Installed:
  nmap.x86_64 2:6.40-7.el7
Complete!
[root@8de7b5e65c98 /]# nmap 8.8.8.8
Nmap scan report for google-public-dns-a.google.com (8.8.8.8)
Host is up (0.0034s latency).
...
[root@8de7b5e65c98 /]# exit
exit
#
```
Although the container is no longer running once you exit, the container still exists with the new software package still installed. 
```
# docker start -ai centos_bash
[root@8de7b5e65c98 /]# nmap 8.8.8.8
Nmap scan report for google-public-dns-a.google.com (8.8.8.8)
Host is up (0.0045s latency).
...
```

## Inspecting a container
To inspect a container, use the ``inspect`` command
```
# docker inspect webserver
```

See logs from a running container as in ``tailf`` mode
```
# docker logs -f webserver
AH00558: httpd: Could not reliably determine the server's fully qualified domain name
Set the 'ServerName' directive globally to suppress this message
```

Examine the processes running inside a container
```
# docker top webserver
UID   PID   PPID    C       STIME     TTY     TIME      CMD
root  12159 12148   0       22:59     ?       00:00:00  httpd -DFOREGROUND
...   ...   ...     ...     ...       ...     ...       ...
```

See the ports used by a daemonized container
```
# docker port webserver
80/tcp -> 0.0.0.0:80
```

To investigate within a running Docker container from the host machine, use the docker ``exec`` command. With docker exec, you can run a command, such as ``/bin/bash`` to enter a running Docker container process to investigate. The reason for using docker exec, instead of just launching the container into a bash shell, is that you can investigate the container as it is running its intended application. By attaching to the container as it is performing its intended task, you get a better view of what the container actually does, without necessarily interrupting the container’s activity.

Start a web server container in daemonized mode
```
# docker run -d -p 80:80 --name web httpd
```

From the host machine, attach a bash shell into the container and interactively, see what is happening into the container
```
# docker exec -it web /bin/bash
root@267ef3db09e5:/usr/local/apache2# pwd
/usr/local/apache2
root@267ef3db09e5:/usr/local/apache2# cat /etc/*release
PRETTY_NAME="Debian GNU/Linux 8 (jessie)"
...
root@267ef3db09e5:/usr/local/apache2# ps -ef
UID        PID  PPID  C STIME TTY          TIME CMD
root         1     0  0 17:07 ?        00:00:00 httpd -DFOREGROUND
daemon       6     1  0 17:07 ?        00:00:00 httpd -DFOREGROUND
daemon       7     1  0 17:07 ?        00:00:00 httpd -DFOREGROUND
daemon       8     1  0 17:07 ?        00:00:00 httpd -DFOREGROUND
root        90     0  0 17:09 ?        00:00:00 /bin/bash
root        94    90  0 17:10 ?        00:00:00 ps -ef
...
root@267ef3db09e5:/usr/local/apache2# uname -r
3.10.0-327.18.2.el7.x86_64

root@267ef3db09e5:/usr/local/apache2# free -m
             total       used       free     shared    buffers     cached
Mem:          3791        633       3158          8          2        412
-/+ buffers/cache:        218       3573
Swap:         1637          0       1637
root@267ef3db09e5:/usr/local/apache2# exit
exit
#
```
The commands just run from the bash shell, running inside the container, show you several things. The container holds a Debian GNU/Linux 8 system. The process table shows that the httpd command is process ID 1 followed by other httpd processes, ``/bin/bash`` is PID 90 and ``ps -ef`` is PID 94. Processes running in the host process table cannot be seen from within the container. There is no separate kernel running in the container since ``uname -r`` shows the host kernel: ``3.10.0-229.1.2.el7.x86_64``. Viewing memory with ``free -m`` command shows the available memory on the host although the container can be limited.

How to run a C program inside a container?
```
# docker pull centos:latest

# docker run -it centos
[root@f679ab7a4bea /]# yum update -y
[root@f679ab7a4bea /]# yum install -y gcc
[root@f679ab7a4bea /]# vi hello.c
int main() {
  printf("Hello Docker\n");
}
[root@f679ab7a4bea /]#  gcc -w hello.c -o hello
[root@f679ab7a4bea /]# ls -lrt hello*
-rw-r--r-- 1 root root   41 May  1 21:08 hello.c
-rwxr-xr-x 1 root root 8512 May  1 21:17 hello

[root@f679ab7a4bea /]# ./hello
Hello Docker
```

## Main Docker commands
The following table, taken from the "*docker help*" command, provides a quick summary of Docker command for working with containers 

| Command  |  Description
|----------|-----------------------------------------------------------------------|
| attach   | Attach to a running container
| commit   | Create a new image from a container's changes
| cp       | Copy files/folders from a container's filesystem to the host path
| diff     | Inspect changes on a container's filesystem
| events   | Get real time events from the server
| export   | Stream the contents of a container as a tar archive
| info     | Display system-wide information
| inspect  | Return low-level information on a container
| kill     | Kill a running container
| load     | Load an image from a tar archive
| logs     | Fetch the logs of a container
| port     | Lookup the public-facing port that is NAT-ed to PRIVATE_PORT
| pause    | Pause all processes within a container
| ps       | List containers
| restart  | Restart a running container
| rm       | Remove one or more containers
| run      | Run a command in a new container
| start    | Start a stopped container
| stop     | Stop a running container
| top      | Lookup the running processes of a container
| unpause  | Unpause a paused container
| version  | Show the Docker version information
| wait     | Block until a container stops, then print its exit code
