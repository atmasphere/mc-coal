#!/bin/bash
PID=`cat server.pid`
if [ "$PID" != "" ]; then
  echo "Stopping MineCraft Server PID=$PID"
  echo save-all >> command-fifo
  echo stop >> command-fifo
  while kill -0 "$PID" > /dev/null 2>&1; do sleep 0.5; done
  rm server.pid
  echo "MineCraft shutdown complete."
else
  echo "MineCraft not running"
fi
