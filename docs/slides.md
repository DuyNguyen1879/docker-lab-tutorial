class: title

# Docker Lab Tutorial

---
# Content

1. Linux Containers

2. Starting with Containers

3. Working with Images

4. Storage

5. Networking

6. Swarm Mode

7. Application Deployment

8. Security

9. Administration

10. Application Programming Interfaces

---
# Linux Container

- Docker project provides the means of packaging applications in lightweight Linux containers

- A container is a system process hiding themself from other processes/containers on the same machine.

- Docker uses standard Linux kernel features to do this.

- Containers existed in Linux/Unix before anyone cared of them, Docker just made using them easier and mass adoption followed.

---
- ***chroot:*** first form of container. A technique in Linux and Unix systems that changes the root directory of a process and all its children. A program that is run in such environment cannot access files and commands outside the chroot directory tree. This modified environment is also called a *jail*.

- ***cgroups:***  an abbreviation for control groups. It is a Linux kernel feature that limits and isolates the resource usage like CPU, memory, disk I/O, network, etc. of a collection of processes.

- ***namespaces:*** a technique to allow sandboxing of resources like processes, networks, users, mounts, and others. Multiple manespaces can be set on the same Linux machine providing a complete isolation of these resources.  

---
Running an application within a container offers the following advantages:

  - Images contain only the content needed to run the application. Saving and sharing is much more efficient with containers than with virtual machines which include the whole operating system.

  - Improved performance since it is not running an entirely separate operating system. A container typically runs faster than a virtual machine.

  - Container typically has its own network interfaces, file system, and memory so the application running in that container can be isolated and secured from other processes on the host machine.

  - With the application runtime included in the container, a Docker container is capable of being run in multiple environments without any changes.

---
# Starting with Containers

---
# Working with Images

---
# Storage

---
# Networking

---
# Swarm Mode

---
# Application Deployment

---
# Security

---
# Administration

---
# Application Programming Interfaces















