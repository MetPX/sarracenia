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
      return 1
   else
      printf "test %2d success: ${3}\n" ${tno}
      return 0
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

if [ "$1" ]; then
   smin=$1
else
   smin=1000
fi

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

if [ "`sr_shovel t_dd1 status |& tail -1 | awk ' { print $8 } '`" != 'stopped' ]; then 
   echo "stopping shovels and waiting..."
   sr_shovel t_dd1 stop
   sr_shovel t_dd2 stop
   sleep 60
fi





tno=0

if [ "${totshovel2}" -gt "${totshovel1}" ]; then
   maxshovel=${totshovel2}
else 
   maxshovel=${totshovel1}
fi
printf "\tmaximum of the shovels is: ${maxshovel}\n\n"


calcres "${totshovel1}" "${totshovel2}" "shovels t_dd1 ( ${totshovel1} ) and t_dd2 ( ${totshovel2} ) should have about the same number of items read"  



t2=$(( ${totsarra}*2 ))

calcres ${totwinnow} ${t2} "sarra tsarra ($totsarra) should be reading about half as many items as (both) winnows (${totwinnow})" 

calcres  ${totsarra} ${totsub} "tsarra (${totsarra}) and sub t (${totsub}) should have about the same number of items" 

calcres ${maxshovel} ${totsub} "max shovel (${maxshovel}) and sub t (${totsub}) should have about the same number of items" 

# this test fails a lot, because it's wrong... if we did it with 3, it would work, but some data has no checksum, so
# there is always more in 00 than in any other.  if we could compare 01 and 02, it would probably work.
#calcres ${totwinnow00} ${totwinnow01} \
#   "winnow00 and (${totwinnow00}) and winnow01 (${totwinnow01}) should have about the same number of items" 

calcres ${maxshovel} ${totsub} "max shovel (${maxshovel}) and subscriber t (${totsub}) should have about the same number of items" 

calcres ${totshortened} ${totsub} \
   "count of truncated headers (${totshortened}) and subscribed messages (${totsub}) should have about the same number of items"

calcres ${totsubr} ${totsub} "count of downloads by subscribe (${totsubr}) and messages received (${totsub}) should be about the same" 

while ! calcres ${totsubr} ${totwatch}  "downloads by subscribe (${totsubr}) and files posted by sr_watch (${totwatch}) should be about the same" ; do
    printf "info: waiting for totwatch to catchup\n"
    sleep 30
    oldtotwatch=${totwatch}
    countall
    if [ "${oldtotwatch}" -eq "${totwatch}"  ]; then
       printf "error: giving up on this test\n"
       break
    fi
done

calcres ${totwatch} ${totsent} "posted by watch(${totwatch}) and sent by sr_sender (${totsent}) should be about the same"
