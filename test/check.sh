#!/bin/bash


totsarra="`grep msg_total ~/.cache/sarra/var/log/sr_log_tsarra_0001.log | tail -1 | awk ' { print $5; }; '`"
totwinnow00="`grep msg_total ~/.cache/sarra/var/log/sr_log_twinnow00_0001.log | tail -1 | awk ' { print $5; }; '`"
totwinnow01="`grep msg_total ~/.cache/sarra/var/log/sr_log_twinnow01_0001.log | tail -1 | awk ' { print $5; }; '`"
totwinnow=$(( $totwinnow00 + $totwinnow01 ))
totsub="`grep msg_total ~/.cache/sarra/var/log/sr_subscribe_t_0001.log | tail -1 | awk ' { print $5; }; '`"
totshovel1="`grep msg_total ~/.cache/sarra/var/log/sr_shovel_t_dd1_0001.log | tail -1 | awk ' { print $5; }; '`"
totshovel2="`grep msg_total ~/.cache/sarra/var/log/sr_shovel_t_dd2_0001.log | tail -1 | awk ' { print $5; }; '`"

snum=1
smin=1000
printf "initial sample building sample size $totsarra need at least $smin \n"

while [ ! "${totsarra}" ]; do
   sleep 10
   totsarra="`grep msg_total ~/.cache/sarra/var/log/sr_log_tsarra_0001.log | tail -1 | awk ' { print $5; }; '`"
   printf "waiting to start...\n"
done

while [ $totsarra -lt $smin ]; do
   totsarra="`grep msg_total ~/.cache/sarra/var/log/sr_log_tsarra_0001.log | tail -1 | awk ' { print $5; }; '`"
   totwinnow00="`grep msg_total ~/.cache/sarra/var/log/sr_log_twinnow00_0001.log | tail -1 | awk ' { print $5; }; '`"
   totwinnow01="`grep msg_total ~/.cache/sarra/var/log/sr_log_twinnow01_0001.log | tail -1 | awk ' { print $5; }; '`"
   totwinnow=$(( $totwinnow00 + $totwinnow01 ))
   totsub="`grep msg_total ~/.cache/sarra/var/log/sr_subscribe_t_0001.log | tail -1 | awk ' { print $5; }; '`"
   totshovel1="`grep msg_total ~/.cache/sarra/var/log/sr_shovel_t_dd1_0001.log | tail -1 | awk ' { print $5; }; '`"
   totshovel2="`grep msg_total ~/.cache/sarra/var/log/sr_shovel_t_dd2_0001.log | tail -1 | awk ' { print $5; }; '`"
   sleep 10
   printf  "sample now %6d \r"  $totsarra

done



res=$(( ( ${totshovel1}*1000 ) / ${totshovel2} ))
if [ $res -lt 900  -o $res -gt 1100 ]; then
   echo "test 1: FAIL, shovel1 ($totshovel1) should be reading the same number of items as shovel2 (${totshovel2})"
else
   echo "test 1: SUCCESS, shovel1 (${totshovel1}) reading the same as shovel2 (${totshovel2}) does"
fi


res=$(( ( ${totwinnow}*1000 ) / ${totsarra} ))
if [ $res -lt 1900  -o $res -gt 2100 ]; then
   echo "test 2: FAIL, sarra ($totsarra) should be reading about half as many items as winnow (${totwinnow})"
else
   echo "test 2: SUCCESS, winnow (${totwinnow}) reading double what sarra (${totsarra}) does"
fi


res=$(( ( ${totsarra}*1000 ) / ${totsub} ))
if [ $res -lt 900  -o $res -gt 1100 ]; then
   echo "test 3: FAIL, sarra (${totsarra}) and sub (${totsub}) should have about the same number of items"
else
   echo "test 3: SUCCESS, subscribe (${totsub}) has the same number of items as sarra (${totsarra})"
fi

res=$(( ( ${totshovel1}*1000 ) / ${totsub} ))
if [ $res -lt 900  -o $res -gt 1100 ]; then
   echo "test 4: FAIL, shovel1 (${totshovel1}) and sub (${totsub}) should have about the same number of items"
else
   echo "test 4: SUCCESS, subscribe (${totsub}) has the same number of items as shovel1 (${totshovel1})"
fi
