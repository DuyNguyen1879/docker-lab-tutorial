#!/bin/bash
#
# Copyright 2017 - Adriano Pezzuto
# https://github.com/kalise
#
# Make sure the gcloud cli utility is installed and
# initialized with proper credentials
#
# Usage: ./gcloud-create-swarm-env.sh
#

NUM=8

REGION1=europe-west1
ZONE1=europe-west1-c
REGION2=europe-west2
ZONE2=europe-west2-c
NETWORK=swarm
IMAGE=projects/noverit-168407/global/images/swarm-node
ROLE=swarm-node
MACHINE_TYPE=n1-standard-1
TAG=swarm
SCOPES=default,compute-ro,service-control,service-management,logging-write,monitoring-write,storage-ro
FIREWALL_RULES=tcp:22,tcp:443,tcp:80,tcp:8000-8100,tcp:9090

# Create the network
echo "Creating the network" $NETWORK
gcloud compute networks create $NETWORK --mode=custom

# Create firewall rules
echo "Creating firewall rules"
gcloud compute firewall-rules create swarm-allow-internal --network $NETWORK --allow tcp,udp,icmp  --source-ranges 10.10.0.0/16
gcloud compute firewall-rules create swarm-allow-external --network $NETWORK --allow $FIREWALL_RULES

# Create Subnets and Instances
REGION=$REGION1
ZONE=$ZONE1
VMCOUNT=0
VMLIMIT=18
for i in $(seq -w 0 $NUM);
do
  SUBNET=$REGION-swarm-subnet-$(printf "%02.f" $i);
  echo "Creating subnet" $SUBNET "in zone" $REGION
  RANGE=10.10.$(printf "%1.f" $i).0/24
  gcloud compute networks subnets create $SUBNET \
         --network=$NETWORK \
         --range=$RANGE \
         --enable-private-ip-google-access \
         --region=$REGION
  echo "Creating machines in subnet" $SUBNET
  for j in {0..2};
  do
    NAME=docker-user$(printf "%02.f" $i)-node$(printf "%02.f" $j)
    ADDRESS=10.10.$(printf "%1.f" $i).1$(printf "%02.f" $j)
    echo "Creating instance" $NAME "having IP" $ADDRESS
    gcloud compute instances create $NAME \
       --async \
       --boot-disk-auto-delete \
       --boot-disk-type=pd-standard \
       --can-ip-forward \
       --image=$IMAGE \
       --labels=role=$ROLE \
       --machine-type=$MACHINE_TYPE \
       --restart-on-failure \
       --network-interface=network=$NETWORK,subnet=$SUBNET,private-network-ip=$ADDRESS \
       --tags=$TAG \
       --zone=$ZONE \
       --scopes=$SCOPES
    VMCOUNT=$(expr $VMCOUNT + 1)
    if [[ $VMCOUNT -eq $VMLIMIT ]]; then
        REGION=$REGION2
        ZONE=$ZONE2
    fi
  done
  echo "Done with subnet" $SUBNET
done
echo "Done"
