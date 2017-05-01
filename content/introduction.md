# Linux Containers
The Docker project provides the means of packaging applications in lightweight Linux containers. A container is a system process hiding themself from other processes/containers on the same machine. Docker uses standard Linux kernel features to do this. Containers existed in Linux/Unix before anyone cared of them, Docker just made using them easier and mass adoption followed.

Historically, the first form of container was the *chroot*. This is a technique in Linux and Unix systems that changes the root directory of the current running process and all their children. The process running in a chroot will not know about the real filesystem root
directory. A program that is run in such environment cannot access files and commands outside the chroot directory tree. This modified environment is called a chroot jail.

Another step-stone in Linux containers was the introduction of *cgroups*, an abbreviation for control groups. It is a Linux kernel feature that limits and isolates the resource usage like CPU, memory, disk I/O, network, etc. of a collection of processes.

The next step in Linux container history was the introduction of LXC or Linux container. LXC leverages on cgroups and other *namespace* techniques to allow sandboxing processes from each another, and controlling their resource allocations. First versions of Docker were based on LXC but it was soon replaced by Docker own *libcontainer* library written in the Go programming language.

Running an application within a container offers the following advantages:

   * Images contain only the content needed to run the application. Saving and sharing is much more efficient with containers than with virtual machines which include the whole operating system.

   * Improved performance since it is not running an entirely separate operating system. A container typically runs faster than a virtual machine.

   * Container typically has its own network interfaces, file system, and memory so the application running in that container can be isolated and secured from other processes on the host machine.
   
   * With the application runtime included in the container, a Docker container is capable of being run in multiple environments without any changes.

Main things to understand here are:

* an *image* is a specific state of a filesystem
* an image is composed of *layers* representing changes in the filesystem at various points in time
* a *container* is a running process that is started based on an given image
* changes in the filesystem of a container can be committed to create a new image
* changes in memory cannot be committed, only changes on the filesystem
