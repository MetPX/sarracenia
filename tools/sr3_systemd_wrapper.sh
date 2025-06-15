#!/bin/bash
#
operation=$1

if [ "$operation" == "start" ]; then
   configs="`sr3 status| awk ' ( $2 ~ /stop|new/ ) { print $1; } '|sed s+/+-+`"
else
   # "stop", "restart" , "status"
   configs="`sr3 status| awk ' ( $2 ~ /cpuS|hung|idle|lag|part|run|slow|stby|unkn|wVip/ ) { print $1; } '|sed s+/+-+`"
fi

for flow in ${configs}; do
      systemctl --user ${operation} metpx-sr3@${flow}.service &
done
