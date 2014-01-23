#!/bin/bash
rm -f command-fifo
mkfifo -m 0666 command-fifo
java -Xmx1G -Xms1G -Dlog4j.configurationFile=log4j2.xml -jar minecraft_server.jar nogui <> command-fifo &
echo $! >| server.pid
