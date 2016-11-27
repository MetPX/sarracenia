#!/bin/bash

function countthem {
   if [ ! "${1}" ]; then
      tot=0
   else
      tot="${1}"
   fi
}

function countall {

  countthem "`grep msg_total ~/.cache/sarra/log/sr_report_tsarra_0001.log | tail -1 | awk ' { print $5; }; '`" 
  totsarra="${tot}"

  countthem "`grep msg_total ~/.cache/sarra/log/sr_report_twinnow00_0001.log | tail -1 | awk ' { print $5; }; '`"
  totwinnow00="${tot}"

  countthem "`grep msg_total ~/.cache/sarra/log/sr_report_twinnow01_0001.log | tail -1 | awk ' { print $5; }; '`"
  totwinnow01="${tot}"
   
  totwinnow=$((${totwinnow00} + ${totwinnow01}))

  countthem "`grep msg_total ~/.cache/sarra/log/sr_subscribe_t_0001.log | tail -1 | awk ' { print $5; }; '`"
  totsub="${tot}"

  countthem "`grep file_total ~/.cache/sarra/log/sr_subscribe_t_0001.log | tail -1 | awk ' { print $5; }; '`"
  totsubr="${tot}"

  countthem "`grep msg_total ~/.cache/sarra/log/sr_shovel_t_dd1_0001.log | tail -1 | awk ' { print $5; }; '`"
  totshovel1="${tot}"

  countthem "`grep msg_total ~/.cache/sarra/log/sr_shovel_t_dd2_0001.log | tail -1 | awk ' { print $5; }; '`"
  totshovel2="${tot}"

  countthem "`grep post_total ~/.cache/sarra/log/sr_watch_sub_0001.log | tail -1 | awk ' { print $5; }; '`"
  totwatch="${tot}"

  countthem "`grep truncating ~/.cache/sarra/log/sr_sarra_download_000*.log | wc -l`"
  totshortened="${tot}"

  countthem "`grep Sends: ~/.cache/sarra/log/sr_sender_tsource2send_000*.log | wc -l`"
  totsent="${tot}"
}


countall

snum=1
smin=1000
printf "initial sample building sample size $totsarra need at least $smin \n"

while [ "${totsarra}" == 0 ]; do
   sleep 10
   countthem "`grep msg_total ~/.cache/sarra/log/sr_report_tsarra_0001.log | tail -1 | awk ' { print $5; }; '`" 
   totsarra="${tot}"
   printf "waiting to start...\n"
done

while [ $totsarra -lt $smin ]; do
   sleep 10

   countall

   printf  "sample now %6d \r"  $totsarra

done



tno=1
res=0
res=$(( ( ${totshovel1}*1000 ) / ${totshovel2} ))
if [ $res -lt 900  -o $res -gt 1100 ]; then
   echo "test ${tno}: FAIL, shovel1 ($totshovel1) should be reading the same number of items as shovel2 (${totshovel2})"
else
   echo "test ${tno}: SUCCESS, shovel1 (${totshovel1}) reading the same as shovel2 (${totshovel2}) does"
fi

tno=$((${tno}+1))
res=0
res=$(( ( ${totwinnow}*1000 ) / ${totsarra} ))
if [ $res -lt 1900  -o $res -gt 2100 ]; then
   echo "test ${tno}: FAIL, sarra ($totsarra) should be reading about half as many items as winnow (${totwinnow})"
else
   echo "test ${tno}: SUCCESS, winnow (${totwinnow}) reading double what sarra (${totsarra}) does"
fi


tno=$((${tno}+1))
res=0
res=$(( ( ${totsarra}*1000 ) / ${totsub} ))
if [ $res -lt 900  -o $res -gt 1100 ]; then
   echo "test ${tno}: FAIL, sarra (${totsarra}) and sub (${totsub}) should have about the same number of items"
else
   echo "test ${tno}: SUCCESS, subscribe (${totsub}) has the same number of items as sarra (${totsarra})"
fi

tno=$((${tno}+1))
res=0
res=$(( ( ${totshovel1}*1000 ) / ${totsub} ))
if [ $res -lt 900  -o $res -gt 1100 ]; then
   echo "test ${tno}: FAIL, shovel1 (${totshovel1}) and sub (${totsub}) should have about the same number of items"
else
   echo "test ${tno}: SUCCESS, subscribe (${totsub}) has the same number of items as shovel1 (${totshovel1})"
fi


tno=$((${tno}+1))
res=0

res00=$(( ${totwinnow00}*1000 / ${totwinnow} ))
res01=$(( ${totwinnow01}*1000 / ${totwinnow} ))

res=$(( ( ${totshovel1}*1000 ) / ${totsub} ))

if [ $res -lt 900  -o $res -gt 1100 ]; then
   echo "test ${tno}: FAIL, shovel2 (${totshovel2}) and sub (${totsub}) should have about the same number of items"
else
   echo "test ${tno}: SUCCESS, subscribe (${totsub}) has the same number of items as shovel2 (${totshovel2})"
fi

tno=$((${tno}+1))
res=0

res=$(( ( ${totshortened}*1000 ) / ${totsub} ))

if [ $res -lt 900  -o $res -gt 1100 ]; then
   echo "test ${tno}: FAIL, count of truncated headers (${totshortened}) and subscribed messages (${totsub}) should have about the same number of items"
else
   echo "test ${tno}: SUCCESS, subscribe (${totsub}) has the same number of items as headers that were truncated (${totshortened})"
fi

tno=$((${tno}+1))
res=0

res=$(( ( ${totsubr}*1000 ) / ${totsub} ))
if [ $res -lt 900  -o $res -gt 1100 ]; then
   echo "test ${tno}: FAIL, count of downloads by subscribe (${totsubr}) and messages received (${totsub}) should be about the same"
else
   echo "test ${tno}: SUCCESS, subscribe messages accepted (${totsub}) is the same as files downloaded (${totsubr})"
fi


tno=$((${tno}+1))
res=0
res=$(( ( ${totsub}*1000 ) / ${totwatch} ))
if [ $res -lt 900  -o $res -gt 1100 ]; then
   echo "test ${tno}: FAIL, messages received by subscribe (${totsub}) and posted by sr_watch (${totwatch}) should be about the same"
else
   echo "test ${tno}: SUCCESS, messages received by subscribe (${totsub}) is the same as files posted (${totwatch}) by watch"
fi

tno=$((${tno}+1))
res=0

res=$(( ( ${totwatch}*1000 ) / ${totsent} ))
if [ $res -lt 900  -o $res -gt 1100 ]; then
   echo "test ${tno}: FAIL, posted by watch(${totwatch}) and sent by sr_sender (${totsent}) should be about the same"
else
   echo "test ${tno}: SUCCESS, posted by watch (${totwatch}) is the same as files sent (${totsent}) by sender"
fi

