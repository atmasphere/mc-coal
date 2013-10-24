#!/bin/bash

apt-get -y install openjdk-7-jre
apt-get -y install python-pip
pip install --upgrade google-api-python-client
mkdir minecraft
cd minecraft
wget https://s3.amazonaws.com/Minecraft.Download/versions/1.6.4/minecraft_server.1.6.4.jar -O minecraft_server.jar
CONTROLLER_SCRIPT=$(curl http://metadata/computeMetadata/v1beta1/instance/attributes/controller-script)
cd ..
mkdir coal
cd coal
printf "$CONTROLLER_SCRIPT" > mc_coal_controller.py
chmod a+x mc_coal_controller.py
