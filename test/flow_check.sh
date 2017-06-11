#!/bin/bash

# The directory we run the flow test scripts in...
tstdir="`pwd`"

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
   # 4 - will retry flag.
   #


   if [ "${1}" -eq 0 ]; then
      printf "test %2d FAILURE: no successful results! ${3}\n" ${tno}
      tno=$((${tno}+1))
      return 2
   fi

   if [ "${2}" -eq 0 ]; then
      printf "test %2d FAILURE: no successful results, 2nd item! ${3}\n" ${tno}
      tno=$((${tno}+1))
      return 2
   fi

   res=0

   mean=$(( (${1} + ${2}) / 2 ))
   maxerr=$(( $mean / 10 ))

   min=$(( $mean - $maxerr ))
   max=$(( $mean + $maxerr ))

   tno=$((${tno}+1))

   if [ $1 -lt $min -o $2 -lt $min -o $1 -gt $max -o $1 -gt $max ]; then
	   printf "test %2d FAILURE: ${3}\n" ${tno}
      if [ "$4" ]; then
         tno=$((${tno}-1))
      fi    
      return 1
   else
      printf "test %2d success: ${3}\n" ${tno}
      passedno=$((${passedno}+1))
      return 0
   fi

}

function tallyres {
   # tallyres - All the results must be good.  99/100 is bad!
   # 
   # logic:
   # increment test number (tno)
   # compare first and second totals, and report agreement if within 10% of one another.
   # emit description based on agreement.  Arguments:
   # 1 - value obtained 
   # 2 - value expected
   # 3 - test description string.

   tno=$((${tno}+1))

   if [ ${1} -ne ${2} -o ${2} -eq 0 ]; then
      printf "test %2d FAILURE: ${1} of ${2}: ${3}\n" ${tno}
      if [ "$4" ]; then
         tno=$((${tno}-1))
      fi    
      return 1
   else
      printf "test %2d success: ${1} of ${2}: ${3}\n" ${tno}
      passedno=$((${passedno}+1))
   fi

}

function countall {

  countthem "`grep msg_total ~/.cache/sarra/log/sr_report_tsarra_0001.log | tail -1 | awk ' { print $5; }; '`" 
  totsarra="${tot}"

  countthem "`grep msg_total ~/.cache/sarra/log/sr_report_twinnow00_0001.log | tail -1 | awk ' { print $5; }; '`"
  totwinnow00="${tot}"

  countthem "`grep msg_total ~/.cache/sarra/log/sr_report_twinnow01_0001.log | tail -1 | awk ' { print $5; }; '`"
  totwinnow01="${tot}"
   
  if [ ${totwinnow00} -gt ${totwinnow01} ]; then
       totwinnow=$(( ${totwinnow00} *2 ))
  else
       totwinnow=$(( ${totwinnow01} *2 ))
  fi

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

  countthem "`grep 'downloaded to:' ~/.cache/sarra/log/sr_subscribe_q_000*.log | wc -l`"
  totsub2="${tot}"
  countthem  "`grep 'post_log notice' ~/.cache/sarra/log/sr_poll_test1_000*.log | wc -l`"
  totpoll1="${tot}"

  countthem "`grep 'downloaded to:' ~/.cache/sarra/log/sr_subscribe_r_000*.log | wc -l`"
  totsub3="${tot}"
  countthem "`grep 'post_log notice' ~/sarra_devdocroot/srpostlogfile.log | wc -l`"
  totpost1="${tot}"

}

# sr_post initial start
httpdocroot=`cat $tstdir/.httpdocroot`
srpostdir=`cat $tstdir/.httpdocroot`/sent_by_tsource2send
srpostlstfile_new=$httpdocroot/srpostlstfile.new
srpostlstfile_old=$httpdocroot/srpostlstfile.old
srpostlogfile=$httpdocroot/srpostlogfile.log

touch ${srpostlogfile}
touch ${srpostlstfile_old}
# sr_post initial end

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

cd $srpostdir

while [ $totsarra -lt $smin ]; do
   if [ "`sr_shovel t_dd1 status |& tail -1 | awk ' { print $8 } '`" == 'stopped' ]; then 
      echo "starting shovels and waiting..."
      sr_shovel t_dd1 start &
      sr_shovel t_dd2 start
   fi
   sleep 10

   # sr_post testing START
   # TODO - consider if .httpdocroot ends with a '/' ?
   ls $srpostdir > $srpostlstfile_new
   # Obtain file listing delta
   srpostdelta=`comm -23 $srpostlstfile_new $srpostlstfile_old`

   if ! [ "$srpostdelta" == "" ]; then
     #sr_post -b amqp://tsource@localhost/ -to ALL -ex xs_tsource_post -u sftp://peter@localhost -dr $srpostdir -p $srpostdelta >> $srpostlogfile 2>&1
     sr_post -c ~/.config/sarra/post/test2.conf  $srpostdelta >> $srpostlogfile 2>&1
   fi

   cp -p $srpostlstfile_new $srpostlstfile_old
   # sr post testing END

   countall

   printf  "sample now %6d \r"  $totsarra

done
printf  "\nSufficient!\n" 

if [ "`sr_shovel t_dd1 status |& tail -1 | awk ' { print $8 } '`" != 'stopped' ]; then 
   echo "stopping shovels and waiting..."
   sr_shovel t_dd2 stop &
   sr_shovel t_dd1 stop
   sleep 30
fi

countall


passedno=0
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

# this test fails a lot, because it's wrong... if we did it with 3, it would work, but some data has no checksum, so
# there is always more in 00 than in any other.  if we could compare 01 and 02, it would probably work.
#calcres ${totwinnow00} ${totwinnow01} \
#   "winnow00 and (${totwinnow00}) and winnow01 (${totwinnow01}) should have about the same number of items" 

calcres ${maxshovel} ${totsub} "max shovel (${maxshovel}) and subscriber t (${totsub}) should have about the same number of items" 

calcres ${totshortened} ${totsub} \
   "count of truncated headers (${totshortened}) and subscribed messages (${totsub}) should have about the same number of items"

calcres ${totsubr} ${totsub} "count of downloads by subscribe (${totsubr}) and messages received (${totsub}) should be about the same" 

while ! calcres ${totsubr} ${totwatch}  "downloads by subscribe (${totsubr}) and files posted by sr_watch (${totwatch}) should be about the same" retry ; do
    printf "info: retrying... waiting for totwatch to catchup\n"
    sleep 30
    oldtotwatch=${totwatch}
    countall
    if [ "${oldtotwatch}" -eq "${totwatch}"  ]; then
       printf "error: giving up on this test\n"
       tno=$((${tno}+1))
       break
    fi
done

calcres ${totwatch} ${totsent} "posted by watch(${totwatch}) and sent by sr_sender (${totsent}) should be about the same"

DR="`cat $tstdir/.httpdocroot`"
good_files=0
all_files=0
cd $DR
echo "" >bad_file.list
for i in `ls sent_by_tsource2send/` ; do
    if cmp downloaded_by_sub_t/$i sent_by_tsource2send/$i >& /dev/null ; then
       good_files=$((${good_files}+1))
    else
       echo $i >>bad_file.list
    fi
    all_files=$((${all_files}+1))
done

tallyres $good_files $all_files "files sent with identical content to those downloaded by subscribe"

tallyres ${totpoll1} ${totsub2} "poll test1 and subscribe q run together. Should have equal results."

calcres ${totpost1} ${totsub3} "post test2 ${totpost1} and subscribe r ${totsub3} run together. Should have equal results."

calcres ${tno} ${passedno} "Overall ${passedno} of ${tno} passed!"

exit $?

