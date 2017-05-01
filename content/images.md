## Working with images
When the client specifies an image, Docker looks first for the image on local host. If the image does not exist locally, then the image is pulled from the public image registry **Docker Hub**. The Docker Hub is responsible for centralizing information about user accounts, images, and public name spaces. Storing the images you create, searching for images you might want, or publishing images are all elements of image management.

  * [Getting started with images](#getting-started-with-images)
  * [Creating an image from a container](#creating-an-image-from-a-container)
  * [Creating an image from a Docker file](#creating-an-image-from-a-docker-file)
  * [Building your own images](#building-your-own-images)

### Getting started with images
Search an image from the Docker Hub
```
# docker search mysql
NAME                       DESCRIPTION                                     STARS     OFFICIAL   AUTOMATED
mysql                      MySQL is a widely used, open-source relati...   2353      [OK]
mysql/mysql-server         Optimized MySQL Server Docker images. Crea...   144                  [OK]
centurylink/mysql          Image containing mysql. Optimized to be li...   45                   [OK]
...
```

Pull an image from the Docker Hub
```
# docker pull mysql/mysql-server
Using default tag: latest
...
Status: Downloaded newer image for mysql/mysql-server:latest
```

List the local images
```
# docker images
REPOSITORY           TAG                 IMAGE ID            CREATED             SIZE
httpd                latest              bf8f39bc3b6b        47 hours ago        194.5 MB
centos               latest              8596123a638e        5 days ago          196.7 MB
ubuntu               latest              c5f1cf30c96b        2 weeks ago         120.7 MB
mysql/mysql-server   latest              de3969c3af1c        4 weeks ago         296.7 MB
busybox              latest              47bcc53f74dc        9 weeks ago         1.113 MB
```

Start a container from the local image
```
# docker run -it centos
```

Remove a locally stored image
```
# docker rmi mysql/mysql-server
Untagged: mysql/mysql-server:latest
Deleted: sha256:de3969c3af1c0d7538ce052695e64d9afc4e777569bd5ca61b0440da14fbfd4a
...
```

### Creating an image from a container
In the following, we are going to describes how to create a new image from an existing image and a set of packages of choose, for example the Apache Web server.

Pull the base CentOS image from the Docker Hub
```
# docker pull centos:latest
```

Start the container in interactive mode and install the Apache Web Server
```
# docker run -it --name centos_with_httpd centos
[root@3b929be30cb2 /]# yum update -y; yum install -y httpd; yum clean all
[root@3b929be30cb2 /]# systemctl enable httpd
[root@3b929be30cb2 /]# echo ServerName apache.example.com >> /etc/httpd/conf/httpd.conf
[root@3b929be30cb2 /]# echo Hello Docker > /var/www/html/index.html
[root@3b929be30cb2 /]# exit
```

Commit the changes to a new local image
```
# docker commit -m "CentOS base image with Apache Web Server installed" centos_with_httpd myhttpd
# docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
myhttpd             latest              fb6b21fd89c3        39 seconds ago      246.8 MB
centos              latest              8596123a638e        5 days ago          196.7 MB
```

Run a container from the new image just created
```
# docker run -d -p 80:80 --name myweb myhttpd /usr/sbin/httpd -DFOREGROUND
```

Attach a bash to the running container and check the running processes
```
# docker exec -it myweb /bin/bash
[root@58076c84093f /]#
[root@58076c84093f /]#
[root@58076c84093f /]#
[root@58076c84093f /]# ps -ef
UID        PID  PPID  C STIME TTY          TIME CMD
root         1     0  0 18:14 ?        00:00:00 /usr/sbin/httpd -DFOREGROUND
apache       5     1  0 18:14 ?        00:00:00 /usr/sbin/httpd -DFOREGROUND
apache       6     1  0 18:14 ?        00:00:00 /usr/sbin/httpd -DFOREGROUND
apache       7     1  0 18:14 ?        00:00:00 /usr/sbin/httpd -DFOREGROUND
apache       8     1  0 18:14 ?        00:00:00 /usr/sbin/httpd -DFOREGROUND
apache       9     1  0 18:14 ?        00:00:00 /usr/sbin/httpd -DFOREGROUND
root        10     0  0 18:19 ?        00:00:00 /bin/bash
root        21    10  0 18:19 ?        00:00:00 ps -ef
```

Now that you see the new image is working, let's to make it of public domain by pushing the image on the Docker Hub. This step assume you already have an account on the Docker Hub.

Tag the new image with the namespace associated with your account
```
# docker tag myhttpd kalise/myhttpd:latest
# docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
kalise/myhttpd      latest              b48380ba8a9b        26 minutes ago      246.8 MB
myhttpd             latest              b48380ba8a9b        26 minutes ago      246.8 MB
centos              latest              8596123a638e        5 days ago          196.7 MB
```

Login to the Docker Hub and push the image
```
# docker login --username=kalise --password=********
Login Succeeded
# docker push kalise/myhttpd:latest
The push refers to a repository [docker.io/kalise/myhttpd]
138fc78301b9: Pushed
5f70bf18a086: Mounted from kalise/httpd
```

### Creating an image from a Docker file
Building container images from Dockerfile files is the preferred way to create Docker well formatted containers, as compared to modifying running containers and committing them to images. The procedure here involves creating a Dockerfile file to build our own Apache Web Server image based on CentOS base image:

1. Choosing a base image
2. Install the packages needed for an Apache Web server
3. Map the server port to a specied port on the host
4. Launch the Web server

Create the project directory and edit a text file called Dockerfile

```
# mkdir -p httpd-project
# cd httpd-project
# touch Dockerfile
```

The Dockerfile will be like this
```
# My HTTP Docker image
# Version 1

# Pull the CentOS 7.2 image from the Docker Hub registry
FROM centos:7

MAINTAINER Tom Cat
USER root

# Update packages list and install some useful tools
RUN yum update -y

# Add the httpd package
RUN yum install -y httpd

# Clean the yum cache
RUN yum clean all

# Set the Web Server name
RUN echo ServerName apache.example.com >> /etc/httpd/conf/httpd.conf

# Create an index.html file
RUN echo Your Web server is successful > /var/www/html/index.html
```

To build the image from the Dockerfile file, use the build option and identify the location of the Dockerfile file. In this case, the Dockerfile is in the current directory
```
# docker build -t myapache:centos .
```

Check the new image has been created with name ``myapache`` and tag ``centos``
```
# docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
myapache            centos              63d1feab2644        46 seconds ago      224.1 MB
centos              7                   8596123a638e        6 days ago          196.7 MB
```

Start a container from that image and check it is working
```
# docker run -d -p 80:80 --name myweb myapache:centos /usr/sbin/httpd -DFOREGROUND
# curl localhost:80
Your Web server is successful
```

Tag the image
```
# docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
myapache            centos              f297cdf1a74a        53 minutes ago      314.2 MB

# docker tag myapache:centos kalise/myapache:latest

# docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
kalise/myapache     latest              f297cdf1a74a        55 minutes ago      314.2 MB
myapache            centos              f297cdf1a74a        55 minutes ago      314.2 MB
```

By tagging images, you can add names to make more intuitive to understand what they contain. The Docker tagging command is, essentially, an alias to the image.

The image just created can be pushed on the Docker Hub or it can be saved to a tarball
```
# docker save -o myapache.tar kalise/myapache:latest
```

### Building your own images
Docker can build images automatically by reading the instructions from a Dockerfile. A Dockerfile is a text document that contains all the commands a user could use on the command line to assemble an image. Users can create an automated process that executes several instructions in succession to build its own image.

Starting with a basic Docker file we are going to assemble a complete working image for an HTTP Web Server

```
# My HTTP Docker image: version 1.0

# Pull the CentOS 7.2 image from the Docker Hub registry
FROM centos:7

MAINTAINER Tom Cat tom.cat@warnerbros.com
LABEL Version 1.0
USER root

# Update packages list and install some useful tools
RUN yum update -y

# Add the httpd package
RUN yum install -y httpd

# Clean the yum cache
RUN yum clean all

# Set the Web Server name
RUN echo ServerName apache.example.com >> /etc/httpd/conf/httpd.conf

# Create an index.html file
RUN echo Your Web server is successful > /var/www/html/index.html
```

The ``FROM`` statement sets the base image for subsequent instructions. A valid Dockerfile must have FROM as its first instruction. The image can be any valid image from the public or private repositories. In our case we are starting from a CentOS image as base image for our Web Server.

The ``MAINTAINER`` statement sets the Author field of the generated images.

The ``LABEL`` statement labels the image with a user defined text string.

The ``USER`` statement sets the user name or UID to use when running the image.

The ``RUN`` statement executes any commands in a new layer on top of the current image and commit the results. The resulting committed image will be used for the next step in the Dockerfile. To avoid a neww layer to be added for each RUN statement, multiple RUN statements can be combined in a single instruction. To make the Dockerfile more readable, understandable, and maintainable, split long or complex RUN statements on multiple lines separated with backslashes. Basing on these suggestions, a new version of our Dockerfile may look like this:

```
# My HTTP Docker image: version 1.1

# Pull the CentOS 7.2 image from the Docker Hub registry
FROM centos:7

MAINTAINER Tom Cat tom.cat@warnerbros.com
LABEL Version 1.1
USER root

# Update packages list and install the httpd package
RUN yum update -y && yum install -y httpd && yum clean all

# Set the Web Server name and create an index.html file
RUN \
echo ServerName apache.example.com >> /etc/httpd/conf/httpd.conf && \
echo Your Web server is successful > /var/www/html/index.html
```

To start containers in daemon mode, Docker introduce the ``EXPOSE`` command. The EXPOSE statement sets the container listen on the specified network ports at runtime. You can expose one port number and publish it externally to another host port number. In our case, the default port of the Apache daemon is set to port 80 or port 443. The ``CMD`` statement is used to run the application contained by the image, along with any required parameter. The CMD instruction is recommended for any service-based image. A new version of our Dockerfile may be:
```
# My HTTP Docker image: version 1.2

# Pull the CentOS 7.2 image from the Docker Hub registry
FROM centos:7

MAINTAINER Tom Cat tom.cat@warnerbros.com
LABEL Version 1.2
USER root
EXPOSE 80

# Update packages list and install the httpd package
RUN yum update -y && yum install -y httpd && yum clean all

# Set the Web Server name and create an index.html file
RUN \
echo ServerName apache.example.com >> /etc/httpd/conf/httpd.conf && \
echo Your Web server is successful > /var/www/html/index.html

# Start the Apache web server application at runtime
CMD ["/usr/sbin/apachectl", "-DFOREGROUND"]
```

Docker builds an image from a Dockerfile and a context. The build context consists of the files at a specified location PATH or URL. The PATH is a directory on your local filesystem. The URL is a the location of a Git repository. The ``COPY`` statement copies new files or directories from the source PATH location and adds them to the filesystem of the container at the destination. Multiple resource files may be specified but they must be relative to the source directory, ie.e the context of the build. 

For example, we want to set the default index.html page of our Apache web server to a custom index.html page. Put the custom page in the context of image build
```
# cd /root/httpd-centos
# vi index.html
<!DOCTYPE html>
<html>
<body><h1>Hello Docker!</h1></body>
</html>
```

Change the above Dockerfile to be like this
```
# My HTTP Docker image: version 1.3

# Pull the CentOS 7.2 image from the Docker Hub registry
FROM centos:7

MAINTAINER Tom Cat tom.cat@warnerbros.com
LABEL Version 1.3
USER root
EXPOSE 80

# Update packages list and install the httpd package
RUN yum update -y && yum install -y httpd && yum clean all

# Set the Web Server name
RUN echo ServerName apache.example.com >> /etc/httpd/conf/httpd.conf

# Overwrite the default index.html page
COPY index.html /var/www/html/index.html

# Start the Apache web server application at runtime
CMD ["/usr/sbin/apachectl", "-DFOREGROUND"]
```

Change to the build context and build the image
```
# cd /root/httpd-centos
# ls -l
total 8
-rw-r--r-- 1 root root 582 May 24 15:42 Dockerfile
-rw-r--r-- 1 root root  67 May 24 16:09 index.html
# docker build -t myapache:centos .
# docker run -d -p 80:80 --name web myapache:centos
# docker images
REPOSITORY          TAG                 IMAGE ID            CREATED             SIZE
myapache            latest              b5cfdf80a528        8 minutes ago       246.8 MB
centos              7                   8596123a638e        6 days ago          196.7 MB
```

Start a container based on that image and check it works
```
# docker run -d -p 80:80 --name web myapache
# curl localhost
<!DOCTYPE html>
<html>
<body><h1>Hello Docker!</h1></body>
</html>
```

General guidelines

1. Avoid installing unnecessary packages
2. Run only one process per container
3. Minimize the number of layers

## Building C Applications
In this example, we're going to create a simple docker image running a C application. This is only for demo purpouse.
Move to the app directory and create your C program

    mkdir mycapp
    cd mycapp
    vi hello.c
    int main() {
      printf("Hello Docker\n");
    }

Create a Dockerfile like the following

    # A simple C application
    # Pull a GCC image from the Docker Hub registry
    FROM gcc:latest
    MAINTAINER Tom Cat tom.cat@warnerbros.com
    LABEL Version 1.0
    USER root
    COPY ./hello.c /usr/src/hello.c
    WORKDIR /usr/src
    # Compile the C application
    RUN gcc -w hello.c -o hello
    # Start the C application at runtime
    CMD ["./hello"]

Build your image

    docker build -t capp:1.0 .
    docker images
    REPOSITORY      TAG                 IMAGE ID            CREATED              SIZE
    capp            1.0                 70ab671e4cb1        14 seconds ago       1.49 GB

Run the application

    docker run -it capp:1.0
    Hello Docker

Please, note the size of 1.49 GB for the above image. This is because we compiled un image including the complete GCC envinronment. Absolutely, this is not the best way to build C based applications.

## Building Java Applications
In this section, we're going to build a simple Hello World Java application.
Move to the app directory and create your Java program

    mkdir myjapp
    cd myjapp
    vi hello.java
    class hello {
      public static void main(String []args) {
      System.out.println("Hello Java");
      }
    }

Create a Dockerfile like the following

    # A simple JAVA application
    # Pull a JAVA image from the Docker Hub registry
    FROM java:latest
    MAINTAINER Tom Cat tom.cat@warnerbros.com
    LABEL Version 1.0
    USER root
    COPY ./hello.java /usr/src/hello.java
    WORKDIR /usr/src
    # Compile the JAVA application
    RUN javac hello.java 
    # Start the JAVA application at runtime
    CMD  ["java", "hello"]

Build your image

    docker build -t japp:1.0 .
    docker images
    REPOSITORY           TAG          IMAGE ID            CREATED             SIZE
    japp                 1.0          553c12090fab        22 seconds ago      643.1 MB

Run the application

    docker run -it japp:1.0
    Hello Java

## Building an application server
In this section, we're going to create an application server image based on Tomcat.
Move to the app directory

    mkdir taas
    cd taas

and create a Dockerfile like the following

```
# Create the image from the latest centos image
FROM centos:latest

LABEL Version 1.0
MAINTAINER kalise <https://github.com/kalise/>

ENV TOMCAT='tomcat-7' \
    TOMCAT_VERSION='7.0.75' \
    JAVA_VERSION='1.7.0' \
    USER_NAME='user' \
    INSTANCE_NAME='instance'

# Install dependencies
RUN yum update -y && yum install -y wget gzip tar

# Install JDK
RUN yum install -y java-${JAVA_VERSION}-openjdk-devel && \
yum clean all

# Install Tomcat
RUN wget --no-cookies http://archive.apache.org/dist/tomcat/${TOMCAT}/v${TOMCAT_VERSION}/bin/apache-tomcat-${TOMCAT_VERSION}.tar.gz -O /tmp/tomcat.tgz && \
tar xzvf /tmp/tomcat.tgz -C /opt && \
ln -s  /opt/apache-tomcat-${TOMCAT_VERSION} /opt/tomcat && \
rm /tmp/tomcat.tgz

# Add the tomcat manager users file
ADD ./tomcat-users.xml /opt/tomcat/conf/

# Expose HTTP and AJP ports
EXPOSE 8080 8009

# Mount external volumes for logs and webapps
VOLUME ["/opt/tomcat/webapps", "/opt/tomcat/logs"]

ENTRYPOINT ["/opt/tomcat/bin/catalina.sh", "run"]
```

In the same directory, create the Tomcat users ``tomcat-users.xml`` file as following
```
<?xml version='1.0' encoding='utf-8'?>
<tomcat-users>
  <role rolename="manager-gui"/>
  <user username="tomcat" password="tomcat" roles="tomcat, manager-gui"/>
</tomcat-users>
```

Compile the images

    docker build -t taas:1.0 .
    
Run the container

    docker run -d -p 8080:8080 taas:1.0
    
Point the browser to the exposed port and login to the Tomcat application server.
