#!/usr/bin/env sh

cd "$(dirname "$0")"
echo $$ > server.pid
exec java -Xmx3G -Xms3G -jar minecraft_server.jar
