#!/bin/bash

if [ -z "$1" ]; then
    if id -u _minecraft >/dev/null 2>&1; then
        echo "Users up to date"
    else
        echo "Updating users"
        useradd -m _minecraft
        # Start visudo with this script as first parameter
        export EDITOR=$0 && sudo -E visudo
    fi
else
    echo "root ALL=(_minecraft) NOPASSWD: ALL" >> $1
    exit
fi

sudo sh -c 'echo "deb http://ppa.launchpad.net/webupd8team/java/ubuntu precise main" >> /etc/apt/sources.list'
sudo sh -c 'echo "deb-src http://ppa.launchpad.net/webupd8team/java/ubuntu precise main" >> /etc/apt/sources.list'
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys EEA14886
apt-get update
echo oracle-java8-installer shared/accepted-oracle-license-v1-1 select true | sudo /usr/bin/debconf-set-selections
apt-get -y install oracle-java8-installer
apt-get -y install python-pip
apt-get -y install git
pip install --upgrade google-api-python-client
pip install --upgrade pytz
pip install --upgrade pyyaml
pip install --upgrade requests
pip install --upgrade git+https://github.com/twoolie/NBT@version-1.4.1#egg=NBT

mkdir /coal
/usr/share/google/safe_format_and_mount -m "mkfs.ext4 -F" /dev/disk/by-id/google-coal /coal

cd /coal

PROJECT_ID=$(curl http://metadata/computeMetadata/v1beta1/instance/attributes/project-id)
PROJECT_MC_URL="https://$PROJECT_ID.appspot.com/mc"
echo $PROJECT_ID > project_id

INSTANCE_NAME=$(curl http://metadata/computeMetadata/v1beta1/instance/attributes/instance-name)
echo $INSTANCE_NAME > instance_name

CLIENT_ID=$(curl http://metadata/computeMetadata/v1beta1/instance/attributes/client-id)
echo $CLIENT_ID > client_id

SECRET=$(curl http://metadata/computeMetadata/v1beta1/instance/attributes/secret)
echo $SECRET > secret

TIMEZONES_URL="$PROJECT_MC_URL/timezones.py"
wget $TIMEZONES_URL -O timezones.py

MC_PROP_URL="$PROJECT_MC_URL/server.properties"
wget $MC_PROP_URL -O server.properties

MC_EULA_URL="$PROJECT_MC_URL/eula.txt"
wget $MC_EULA_URL -O eula.txt

LOG4J2_URL="$PROJECT_MC_URL/log4j2.xml"
wget $LOG4J2_URL -O log4j2.xml

AGENT_URL="$PROJECT_MC_URL/mc_coal_agent.py"
wget $AGENT_URL -O mc_coal_agent.py
chmod a+x mc_coal_agent.py

CONTROLLER_URL="$PROJECT_MC_URL/mc_coal_controller.py"
wget $CONTROLLER_URL -O mc_coal_controller.py
chmod a+x mc_coal_controller.py

./mc_coal_controller.py &
