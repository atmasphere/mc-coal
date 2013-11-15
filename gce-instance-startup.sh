#!/bin/bash

apt-get -y install openjdk-7-jre
apt-get -y install python-pip
pip install --upgrade google-api-python-client
pip install pyyaml
pip install requests
pip install psutil
pip install git+https://github.com/twoolie/NBT@version-1.4.1#egg=NBT

MINECRAFT_URL=$(curl http://metadata/computeMetadata/v1beta1/instance/attributes/minecraft-url)
mkdir minecraft
cd minecraft
wget $MINECRAFT_URL -O minecraft_server.jar

cd ..
mkdir coal
cd coal

CONTROLLER_SCRIPT=$(curl http://metadata/computeMetadata/v1beta1/instance/attributes/controller-script)
printf "$CONTROLLER_SCRIPT" > mc_coal_controller.py
chmod a+x mc_coal_controller.py

AGENT_SCRIPT=$(curl http://metadata/computeMetadata/v1beta1/instance/attributes/agent-script)
printf "$AGENT_SCRIPT" > mc_coal_agent.py
chmod a+x mc_coal_agent.py

LOG4J2_CONFIG=$(curl http://metadata/computeMetadata/v1beta1/instance/attributes/log4j2)
printf "$LOG4J2_CONFIG" > log4j2.xml

START_SCRIPT=$(curl http://metadata/computeMetadata/v1beta1/instance/attributes/start-script)
printf "$START_SCRIPT" > mc-start.sh
chmod a+x mc-start.py

STOP_SCRIPT=$(curl http://metadata/computeMetadata/v1beta1/instance/attributes/stop-script)
printf "$STOP_SCRIPT" > mc-stop.sh
chmod a+x mc-stop.py

TIMEZONES=$(curl http://metadata/computeMetadata/v1beta1/instance/attributes/timezones)
printf "$TIMEZONES" > timezones.py
