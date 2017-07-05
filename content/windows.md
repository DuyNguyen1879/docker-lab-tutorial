# Windows Server Containers
In this section, we are going to install Docker on Windows Server 2016. Create a Windows Server 2016 Core Edition machine. You should get the IPADDRESS, the USERNAME and related PASSWORD.

Details on Windows containers are [here](https://docs.microsoft.com/en-us/virtualization/windowscontainers/)

LOgin to the Windows Server machine via RDP (Remote Desktop Protocol) or via PowerShell on your local Windows client.

From a PoweShell:

      PS C:> $credentials = Get-Credential
      PS C:> Enter-PSSession -ComputerName <IPADDRESS> -UseSSL -SessionOption (New-PSSessionOption -SkipCACheck -SkipCNCheck) -Credential $credentials

You will get access to the remote Windows Server Machine PoweShell

## Install Docker on Windows Server
To install Docker on Windows Server, from the PowerShell

      PS C:> Install-Module -Name DockerMsftProvider -Repository PSGallery -Force
      PS C:> Install-Package -Name docker -ProviderName DockerMsftProvider
      PS C:> Restart-Computer -Force

Check and control the status of Docker Daemon

      PS C:> Get-Service docker
      PS C:> Stop-Service docker
      PS C:> Start-Service docker

## Run the Microsoft IIS Web Server as container
We are going to run a Microsoft IIS Web Server as container.

From PowerShell

      PS C:> docker pull microsoft/iis
      PS C:> docker run --name=webserver -d -p 80:80 microsoft/iis

To build a custom image of IIS

      PS C:> mkdir iis
      PS C:> cd iis
      PS C:> notepad .\Dockerfile
      
The Dockerfile will contain this recipe

      # My Microsoft IIS Docker image: version 1.3
      # Pull the Microsoft IIS image from the Docker Hub registry
      FROM microsoft/iis
      # Set the maintainer of this image
      MAINTAINER kalise
      # Set the version
      LABEL Version 1.3
      # Create a custom web site on a given port
      RUN mkdir C:\site
      RUN powershell -NoProfile -Command \
          Import-module IISAdministration; \
          New-IISSite -Name "Site" -PhysicalPath C:\site -BindingInformation "*:8080:"
      # Add HTML content to the site
      COPY index.htm /site/index.htm
      # Expose the port
      EXPOSE 8080

Save the file without extensions.

In the same directory, create a custom ``index.htm`` web page like the following:

      <!DOCTYPE html>
      <html>
      <body><h1>Hello Docker for Windows</h1></body>
      </html>
      
Build the image

      PS C:> docker build -t kalise/iis:latest .
      
And start a container

      PS C:> docker run --name=web -d -p 80:8080 kalise/iis:latest

Check the container is running

      PS C:> docker ps
      CONTAINER ID  IMAGE              COMMAND                  STATUS   PORTS                         NAMES
      e0b5d6698160  kalise/iis:latest  "C:\\ServiceMonitor..."  Up       80/tcp, 0.0.0.0:80->8080/tcp  web


## Run Microsoft SQL Server as container
The Microsoft SQL Server is available as docker container for Windows, details are [here](https://docs.microsoft.com/en-us/sql/linux/sql-server-linux-setup-docker). In this section we are going to run the Express Edition.

From PowerShell

      PS C:> docker pull microsoft/mssql-server-windows-express
      PS C:> docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=*******" -e -d -p 1433:1433 --name=mssql microsoft/mssql-server-windows-express:latest
      
We are using two env varialbles defined in the image to pass EULA acceptance answer and system  dministrator password. Note: make sure to use a Strong!Passw0rd according to MS SQL Server requiremnets.

Check the running containers

      PS C:> docker ps
      CONTAINER ID  IMAGE                COMMAND                  STATUS    PORTS                    NAMES
      4920e0483875  microsoft/mssql-..   "cmd /S /C 'powers..."   Up        0.0.0.0:1433->1433/tcp   mssql


The server is listening on its default port 1433 on both container and host side.

To connect the server from a remote client, use the ``sqlcmd`` on Linux or Windows client

      sqlcmd -S <IPADDRESS>:<PORT> -U SA -P "*******"

Details on accessing a MS SQL server are [here](https://docs.microsoft.com/en-us/sql/linux/sql-server-linux-connect-and-query-sqlcmd).

The MS SQL Server configuration changes and database files are persisted in the container even when restarting the container with ``docker stop`` and ``docker start``. However, removing the container with ``docker rm`` or in case of crash, everything in the container is deleted, including the SQL Server and the databases. To persist changes and user defined databases, use the docker volumes to store data on some host volume.




      
