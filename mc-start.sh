#!/bin/bash
rm -f command-fifo
mkfifo -m 0666 command-fifo
java -Xmx3G -Xms3G -jar minecraft_server.jar nogui <> command-fifo &
echo $! >| server.pid
