#!/bin/bash

apt-get update
apt-get -y install openjdk-7-jre
apt-get -y install python-pip
apt-get -y install python-psutil
apt-get -y install git
pip install --upgrade google-api-python-client
pip install --upgrade pytz
pip install --upgrade pyyaml
pip install --upgrade requests
pip install --upgrade git+https://github.com/twoolie/NBT@version-1.4.1#egg=NBT

useradd -m _minecraft

mkdir /coal
cd /coal

mkdir servers
chown -R _minecraft servers

PROJECT_ID=$(curl http://metadata/computeMetadata/v1beta1/instance/attributes/project-id)
PROJECT_MC_URL="https://$PROJECT_ID.appspot.com/mc"
echo $PROJECT_ID > project_id

TIMEZONES_URL="$PROJECT_MC_URL/timezones.py"
wget $TIMEZONES_URL -O timezones.py

AGENT_URL="$PROJECT_MC_URL/mc_coal_agent.py"
wget $AGENT_URL -O mc_coal_agent.py
chmod a+x mc_coal_agent.py

CONTROLLER_URL="$PROJECT_MC_URL/mc_coal_controller.py"
wget $CONTROLLER_URL -O mc_coal_controller.py
chmod a+x mc_coal_controller.py

MC_PROP_URL="$PROJECT_MC_URL/server.properties"
wget $MC_PROP_URL -O server.properties

LOG4J2_URL="$PROJECT_MC_URL/log4j2.xml"
wget $LOG4J2_URL -O log4j2.xml

./mc_coal_controller.py &
