#!/bin/bash
apt-get -y install openjdk-7-jre
# CONTROLLER_URL=$(curl http://metadata/computeMetadata/v1beta1/instance/attributes/controller-url)
mkdir minecraft
cd minecraft
wget https://s3.amazonaws.com/Minecraft.Download/versions/1.6.4/minecraft_server.1.6.4.jar -O minecraft_server.jar
# wget $CONTROLLER_URL
