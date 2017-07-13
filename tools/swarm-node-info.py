#!/usr/bin/python

# Copyright 2017 - Adriano Pezzuto
# https://github.com/kalise

# Usage: <command> -h host -p port -t
# -h, --host host to connect
# -p, --port port to connect, default is 2375
# -t, --tls use TLS on port 2376

import sys, getopt, os
import docker

def main(argv):
  host = "localhost"
  port = "2375"
  server_timeout = 10
  api_version = 'auto'
  cert_path = os.environ["HOME"] + "/.docker/"
  client_cert = (cert_path + "cert.pem", cert_path + "key.pem")
  ca_cert = cert_path + "ca.pem"
  tls_config = ''
  options, remaining = getopt.getopt(sys.argv[1:], 'h:p:t', ['host=','port=','tls'])
  print "ARGV      :", sys.argv
  print "OPTIONS   :", options
  print "REMAINING :", remaining
  for opt, arg in options:
      if opt in ('-h','--host'):
          host = arg
      elif opt in ('-p','--port'):
          port = arg
      elif opt in ('-t','--tls'):
          tls_config = docker.tls.TLSConfig(client_cert,ca_cert,True)

  base_url = "tcp://" + host + ":" + port
  print "HOST      :", base_url
  client = docker.DockerClient(base_url,api_version,server_timeout,tls_config)
  version = client.version()
  print "VERSION   :", version["Version"]
  print "INFO      :"
  info = client.info()
  template = "{0:16} {1:16} {2:6} {3:6} {4:16} {5:24} {6:16} {7:16} {8:6}"
  print template.format("NAME","VERSION","R/CONT","IMAGES","STORAGE","OPERATING SYSTEM","ARCHITECTURE","MEMORY","CPU")
  if info["Swarm"]["NodeID"]:
     if info["Swarm"]["ControlAvailable"]:
         for node in client.nodes.list():
             node_name = node.attrs["Description"]["Hostname"]
             node_base_url = "tcp://" + node_name + ":" + port
             node_info = docker.DockerClient(node_base_url,api_version,server_timeout,tls_config).info()
             name = node_info["Name"]
             version = node_info["ServerVersion"]
             running = node_info["ContainersRunning"]
             images = node_info["Images"]
             storage = node_info["Driver"]
             nodeos = node_info["OperatingSystem"]
             arch = node_info["Architecture"]
             memory = node_info["MemTotal"]
             cpu = node_info["NCPU"]
             print template.format(name,version,str(running),str(images),storage,nodeos,arch,str(memory),str(cpu))
     else:
         name = info["Name"]
         version = info["ServerVersion"]
         running = info["ContainersRunning"]
         images = info["Images"]
         storage = info["Driver"]
         nodeos = info["OperatingSystem"]
         arch = info["Architecture"]
         memory = info["MemTotal"]
         cpu = info["NCPU"]
         print template.format(name,version,str(running),str(images),storage,nodeos,arch,str(memory),str(cpu))
  else:
    print "Swarm is not active on this node"


if __name__ == "__main__":
  main(sys.argv[1:])

