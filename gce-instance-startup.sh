#!/bin/bash

apt-get -y install openjdk-7-jre
mkdir minecraft
cd minecraft
wget https://s3.amazonaws.com/Minecraft.Download/versions/1.6.4/minecraft_server.1.6.4.jar -O minecraft_server.jar
