#!/bin/bash


totsarra="`grep msg_total ~/.cache/sarra/var/log/sr_report_tsarra_0001.log | tail -1 | awk ' { print $5; }; '`"

totwinnow="`grep msg_total ~/.cache/sarra/var/log/sr_report_twinnow_0001.log | tail -1 | awk ' { print $5; }; '`"
if [ ! "$totwinnow" ]; then
   totwinnow=0
fi

totwinnow00="`grep msg_total ~/.cache/sarra/var/log/sr_report_twinnow00_0001.log | tail -1 | awk ' { print $5; }; '`"
if [ ! "$totwinnow00" ]; then
   totwinnow00=0
fi

totwinnow01="`grep msg_total ~/.cache/sarra/var/log/sr_report_twinnow01_0001.log | tail -1 | awk ' { print $5; }; '`"
if [ ! "$totwinnow01" ]; then
   totwinnow01=0
fi
   
totwinnow=$((${totwinnow} + ${totwinnow00} + ${totwinnow01}))
totsub="`grep msg_total ~/.cache/sarra/var/log/sr_subscribe_t_0001.log | tail -1 | awk ' { print $5; }; '`"
totshovel1="`grep msg_total ~/.cache/sarra/var/log/sr_shovel_t_dd1_0001.log | tail -1 | awk ' { print $5; }; '`"
totshovel2="`grep msg_total ~/.cache/sarra/var/log/sr_shovel_t_dd2_0001.log | tail -1 | awk ' { print $5; }; '`"

snum=1
smin=1000
printf "initial sample building sample size $totsarra need at least $smin \n"

while [ ! "${totsarra}" ]; do
   sleep 10
   totsarra="`grep msg_total ~/.cache/sarra/var/log/sr_report_tsarra_0001.log | tail -1 | awk ' { print $5; }; '`"
   printf "waiting to start...\n"
done

while [ $totsarra -lt $smin ]; do
   sleep 10
   totsarra="`grep msg_total ~/.cache/sarra/var/log/sr_report_tsarra_0001.log | tail -1 | awk ' { print $5; }; '`"
   totwinnow00="`grep msg_total ~/.cache/sarra/var/log/sr_report_twinnow00_0001.log | tail -1 | awk ' { print $5; }; '`"
   totwinnow01="`grep msg_total ~/.cache/sarra/var/log/sr_report_twinnow01_0001.log | tail -1 | awk ' { print $5; }; '`"
   totwinnow=$(( $totwinnow00 + $totwinnow01 ))
   totsub="`grep msg_total ~/.cache/sarra/var/log/sr_subscribe_t_0001.log | tail -1 | awk ' { print $5; }; '`"
   totshovel1="`grep msg_total ~/.cache/sarra/var/log/sr_shovel_t_dd1_0001.log | tail -1 | awk ' { print $5; }; '`"
   totshovel2="`grep msg_total ~/.cache/sarra/var/log/sr_shovel_t_dd2_0001.log | tail -1 | awk ' { print $5; }; '`"
   printf  "sample now %6d \r"  $totsarra

done



tno=1
res=$(( ( ${totshovel1}*1000 ) / ${totshovel2} ))
if [ $res -lt 900  -o $res -gt 1100 ]; then
   echo "test ${tno}: FAIL, shovel1 ($totshovel1) should be reading the same number of items as shovel2 (${totshovel2})"
else
   echo "test ${tno}: SUCCESS, shovel1 (${totshovel1}) reading the same as shovel2 (${totshovel2}) does"
fi

tno=$((${tno}+1))
res=$(( ( ${totwinnow}*1000 ) / ${totsarra} ))
if [ $res -lt 1900  -o $res -gt 2100 ]; then
   echo "test ${tno}: FAIL, sarra ($totsarra) should be reading about half as many items as winnow (${totwinnow})"
else
   echo "test ${tno}: SUCCESS, winnow (${totwinnow}) reading double what sarra (${totsarra}) does"
fi


tno=$((${tno}+1))
res=$(( ( ${totsarra}*1000 ) / ${totsub} ))
if [ $res -lt 900  -o $res -gt 1100 ]; then
   echo "test ${tno}: FAIL, sarra (${totsarra}) and sub (${totsub}) should have about the same number of items"
else
   echo "test ${tno}: SUCCESS, subscribe (${totsub}) has the same number of items as sarra (${totsarra})"
fi

tno=$((${tno}+1))
res=$(( ( ${totshovel1}*1000 ) / ${totsub} ))
if [ $res -lt 900  -o $res -gt 1100 ]; then
   echo "test ${tno}: FAIL, shovel1 (${totshovel1}) and sub (${totsub}) should have about the same number of items"
else
   echo "test ${tno}: SUCCESS, subscribe (${totsub}) has the same number of items as shovel1 (${totshovel1})"
fi


tno=$((${tno}+1))

res00=$(( ${totwinnow00}*1000 / ${totwinnow} ))
res01=$(( ${totwinnow01}*1000 / ${totwinnow} ))

res=$(( ( ${totshovel1}*1000 ) / ${totsub} ))

if [ $res -lt 900  -o $res -gt 1100 ]; then
   echo "test ${tno}: FAIL, shovel1 (${totshovel1}) and sub (${totsub}) should have about the same number of items"
else
   echo "test ${tno}: SUCCESS, subscribe (${totsub}) has the same number of items as shovel1 (${totshovel1})"
fi
