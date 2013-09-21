#!/bin/bash
PID=`cat server.pid`
if [ "$PID" != "" ]; then
  echo "Stopping MineCraft Server PID=$PID"
  echo save-all >> command-fifo
  echo stop >> command-fifo
  wait $PID
  rm server.pid
  echo "MineCraft shutdown complete."
else
  echo "MineCraft not running"
fi
