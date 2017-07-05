# Windows Server Containers

From remote PoweShell:

      $credentials = Get-Credential
      Enter-PSSession -ComputerName 35.190.205.33 -UseSSL -SessionOption (New-PSSessionOption -SkipCACheck -SkipCNCheck) -Credential $credentials

You will get access to the Windows Server Machine PoweShell

## To install Docker on Windows Server

      Install-Module -Name DockerMsftProvider -Repository PSGallery -Force
      Install-Package -Name docker -ProviderName DockerMsftProvider
      Restart-Computer -Force
      Get-Service docker
      Stop-Service docker
      Start-Service docker

## Run IIS WebServer as container

      docker pull microsoft/iis
      docker run --name=webserver -d -p 80:80 microsoft/iis
      docker exec -it webserver cmd
      C:\> echo "Hello Docker for Windows" > C:\inetpub\wwwroot\index.html
      C:\> exit

## Run MS SQL Server Express Edition as container

      docker pull microsoft/mssql-server-windows-express
      docker run -e "ACCEPT_EULA=Y" -e "SA_PASSWORD=<Strong!Passw0rd>" -d -p 1433:1433 --name=mssql microsoft/mssql-server-windows-express:latest
      sqlcmd -S 35.190.205.33 -U SA -P "<Strong!Passw0rd>"
