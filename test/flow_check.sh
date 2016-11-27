#!/bin/bash

function countthem {
   if [ ! "${1}" ]; then
      tot=0
   else
      tot="${1}"
   fi
}

function calcres {
   #
   # calcres - Calculate test result.
   # 
   # logic:
   # increment test number (tno)
   # compare first and second totals, and report agreement if within 10% of one another.
   # emit description based on agreement.  Arguments:
   # 1 - first total
   # 2 - second total 
   # 3 - test description string.
   #

   tno=$((${tno}+1))

   if [ "${1}" -eq 0 ]; then
      printf "test %2d FAILURE: no successful results! ${3}\n" ${tno}
      return
   fi

   res=0
   if [ "${2}" -gt 0 ]; then
         res=$(( ( ${1}*1000 ) / ${2} ))
   fi

   if [ $res -lt 900  -o $res -gt 1100 ]; then
      printf "test %2d FAILURE: ${3}\n" ${tno}
   else
      printf "test %2d success: ${3}\n" ${tno}
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

tno=0

calcres "${totshovel1}" "${totshovel2}" "shovel1 ( ${totshovel1} ) should be reading the same number of items as shovel2 ( ${totshovel2} )" 

t2=$(( ${totsarra}*2 ))
calcres ${totwinnow} ${t2} "sarra ($totsarra) should be reading about half as many items as winnow (${totwinnow})" 

calcres  ${totsarra} ${totsub} "sarra (${totsarra}) and sub (${totsub}) should have about the same number of items" 

calcres ${totshovel1} ${totsub} "shovel1 (${totshovel1}) and sub (${totsub}) should have about the same number of items" 

calcres ${totwinnow00} ${totwinnow01} \
   "winnow00 and (${totwinnow00}) and winnow01 (${totwinnow01}) should have about the same number of items" 

calcres ${totshovel1} ${totsub} "shovel2 (${totshovel2}) and sub (${totsub}) should have about the same number of items" 

calcres ${totshortened} ${totsub} \
   "count of truncated headers (${totshortened}) and subscribed messages (${totsub}) should have about the same number of items"

calcres ${totsubr} ${totsub} "count of downloads by subscribe (${totsubr}) and messages received (${totsub}) should be about the same" 

calcres ${totsub} ${totwatch}  "messages received by subscribe (${totsub}) and posted by sr_watch (${totwatch}) should be about the same"

calcres ${totwatch} ${totsent} "posted by watch(${totwatch}) and sent by sr_sender (${totsent}) should be about the same" 

