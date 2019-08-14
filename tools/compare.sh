#!/bin/bash

client=`basename $1`
client=`echo ${client%%.conf}`

echo $client

cat ~/.cache/sarra/log/sr_sender_${client}_*.log \
    | grep delivered | awk '{print $10}' | sed 's/\/\//\//g' \
    | sort -u > /tmp/sr_${client}

cat ~/convert/log/sundew/*/tx_${client}.log.2019* \
    | grep delivered | awk '{print $10}' |  sed 's/\/\//\//g' \
    | sort -u > /tmp/tx_${client}


echo "NB delivered in sundew = "`wc -l /tmp/tx_${client}`
echo "NB delivered in sarra  = "`wc -l /tmp/sr_${client}`

diff /tmp/tx_${client} /tmp/sr_${client} > /tmp/diff_${client}

echo
echo "INVESTIGATE SR_SENDER SHOULD REJECT"
echo 
cat /tmp/diff_${client} | grep '^>' | sed 's/^.*\///'
echo

echo "INVESTIGATE SR_SENDER MISSING"
echo 
cat /tmp/diff_${client} | grep '^<' | sed 's/^.*\///'
echo 

