# User Namespaces
In Linux, namespaces are essential to the functioning of containers as we know them. The user namespace is a tecnique to maps the UIDs and GIDs inside a container to the regular users and group in the host system.

## Container root user
For example, the PID namespace is what keeps processes in one container from seeing or interacting with processes in another container or, in the host system. A process might have the apparent PID 1 inside a container

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

The container started from the above will run the python ``SimpleHTTPServer`` application as no-root user kalise with UID 1969 and GID 1969

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

This could prevent the user kalise to get any priviledges into the host machine. However, for containers whose processes must run as the root user within the container, we can re-map this user to a less-privileged user on the host. The mapped user is assigned a range of UIDs which function within the namespace as normal UIDs from 0 to 65536, but have no privileges on the host itself. 

## Configure User Namespace
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

To disable the feature, stop the engine, remove the ``"userns-remap": "dummy"`` from the ``/etc/docker/daemon.json`` file and restart the engine.
