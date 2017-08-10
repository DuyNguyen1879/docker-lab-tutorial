# User Namespaces
In Linux, namespaces are essential to the functioning of containers as we know them. For example, the PID namespace is what keeps processes in one container from seeing or interacting with processes in another container or, in the host system. A process might have the apparent PID 1 inside a container

    [root@centos ~]# docker run -it --rm --name ubuntu ubuntu:latest /bin/bash
    root@f1ad1406edd4:/# ps -ef
    UID        PID  PPID  C STIME TTY          TIME CMD
    root         1     0  0 12:47 ?        00:00:00 /bin/bash
    root        11     1  0 12:51 ?        00:00:00 ps -ef

the process will have an ordinary PID on the host system.

    [root@centos ~]# ps -ef | grep bash
    UID        PID  PPID  C STIME TTY          TIME CMD
    ...
    root     23148 12357  0 14:47 pts/0    00:00:00 /usr/bin/docker-current run -it --rm --name ubuntu ubuntu /bin/bash
    root     23316 23305  0 14:47 pts/3    00:00:00 /bin/bash
    root     23354 12429  0 14:53 pts/2    00:00:00 grep --color=auto bash

The PID namespace is responsible for remapping PIDs inside the container. However, in the example above, we see the root user inside the container to be mapped with the root user on the host system. Even the rrot user in container cannot go wild on the host, this could be security hole.

The user namespace is a tecnique to maps the UIDs and GIDs inside a container to the regular users and group in the host system.

