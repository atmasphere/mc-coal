#!/bin/bash

apt-get -y install openjdk-7-jre
apt-get -y install python-pip
pip install --upgrade google-api-python-client
pip install pyyaml
pip install requests
pip install psutil
pip install git+https://github.com/twoolie/NBT@version-1.4.1#egg=NBT

PROJECT_ID=$(curl http://metadata/computeMetadata/v1beta1/instance/attributes/project-id)
printf "$PROJECT_ID" > project_id

MINECRAFT_URL=$(curl http://metadata/computeMetadata/v1beta1/instance/attributes/minecraft-url)
mkdir minecraft
cd minecraft
wget $MINECRAFT_URL -O minecraft_server.jar

cd ..
mkdir coal
cd coal

curl http://metadata/computeMetadata/v1beta1/instance/attributes/controller-script -o mc_coal_controller.py
chmod a+x mc_coal_controller.py

curl http://metadata/computeMetadata/v1beta1/instance/attributes/agent-script -o mc_coal_agent.py
chmod a+x mc_coal_agent.py

curl http://metadata/computeMetadata/v1beta1/instance/attributes/log4j2 -o log4j2.xml

curl http://metadata/computeMetadata/v1beta1/instance/attributes/start-script -o mc-start.py
chmod a+x mc-start.py

curl http://metadata/computeMetadata/v1beta1/instance/attributes/stop-script -o mc-stop.py
chmod a+x mc-stop.py

curl http://metadata/computeMetadata/v1beta1/instance/attributes/timezones -o timezones.py
