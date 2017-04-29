# Linux Containers
The Docker project provides the means of packaging applications in lightweight Linux containers. Containers work by hiding themselves from other processes/containers on the same machine. Docker uses standard Linux kernel features to do this. Containers existed in Linux/Unix before anyone cared of them, Docker just made using them easier and mass adoption followed.

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
