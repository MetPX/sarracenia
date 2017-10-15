#!/bin/bash

function application_dirs {
python3 << EOF
import appdirs

cachedir  = appdirs.user_cache_dir('sarra','science.gc.ca')
cachedir  = cachedir.replace(' ','\ ')
print('export CACHEDIR=%s'% cachedir)

confdir = appdirs.user_config_dir('sarra','science.gc.ca')
confdir = confdir.replace(' ','\ ')
print('export CONFDIR=%s'% confdir)

logdir  = appdirs.user_log_dir('sarra','science.gc.ca')
logdir  = logdir.replace(' ','\ ')
print('export LOGDIR=%s'% logdir)

EOF
}

eval `application_dirs`

C_ALSO="`which sr_cpost`" 

adminpw="`awk ' /bunnymaster:.*\@localhost/ { sub(/^.*:/,""); sub(/\@.*$/,""); print $1; exit }; ' "$CONFDIR"/credentials.conf`"

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


   tno=$((${tno}+1))
   if [ "${1}" -eq 0 ]; then
      printf "test %2d FAILURE: no successful results! ${3}\n" ${tno}
      return 2
   fi

   if [ "${2}" -eq 0 ]; then
      printf "test %2d FAILURE: no successful results, 2nd item! ${3}\n" ${tno}
      return 2
   fi

   res=0

   mean=$(( (${1} + ${2}) / 2 ))
   maxerr=$(( $mean / 10 ))

   min=$(( $mean - $maxerr ))
   max=$(( $mean + $maxerr ))

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

  countthem "`grep msg_total "$LOGDIR"/sr_report_tsarra_0001.log | tail -1 | awk ' { print $5; }; '`" 
  totsarra="${tot}"

  countthem "`grep msg_total "$LOGDIR"/sr_report_twinnow00_0001.log | tail -1 | awk ' { print $5; }; '`"
  totwinnow00="${tot}"

  countthem "`grep msg_total "$LOGDIR"/sr_report_twinnow01_0001.log | tail -1 | awk ' { print $5; }; '`"
  totwinnow01="${tot}"
   
  if [ ${totwinnow00} -gt ${totwinnow01} ]; then
       totwinnow=$(( ${totwinnow00} *2 ))
  else
       totwinnow=$(( ${totwinnow01} *2 ))
  fi

  countthem "`grep msg_total "$LOGDIR"/sr_subscribe_t_f30_0001.log | tail -1 | awk ' { print $5; }; '`"
  totmsgt="${tot}"

  countthem "`grep file_total "$LOGDIR"/sr_subscribe_t_f30_0001.log | tail -1 | awk ' { print $5; }; '`"
  totfilet="${tot}"

  countthem "`grep msg_total "$LOGDIR"/sr_shovel_t_dd1_f00_0001.log | tail -1 | awk ' { print $5; }; '`"
  totshovel1="${tot}"

  countthem "`grep msg_total "$LOGDIR"/sr_shovel_t_dd2_f00_0001.log | tail -1 | awk ' { print $5; }; '`"
  totshovel2="${tot}"

  countthem "`grep post_total "$LOGDIR"/sr_watch_sub_f40_0001.log | tail -1 | awk ' { print $5; }; '`"
  totwatch="${tot}"

  countthem "`grep truncating "$LOGDIR"/sr_sarra_download_f20_000*.log | wc -l`"
  totshortened="${tot}"

  countthem "`grep post_log "$LOGDIR"/sr_sender_tsource2send_f50_000*.log | wc -l`"
  totsent="${tot}"

  countthem "`grep 'downloaded to:' "$LOGDIR"/sr_subscribe_q_f71_000*.log | wc -l`"
  totsubq="${tot}"
  countthem  "`grep 'post_log notice' "$LOGDIR"/sr_poll_test1_f62_000*.log | wc -l`"
  totpoll1="${tot}"

  countthem "`grep 'downloaded to:' "$LOGDIR"/sr_subscribe_r_ftp_f70_000*.log | wc -l`"
  totsubr="${tot}"

  countthem "`grep 'downloaded to:' "$LOGDIR"/sr_subscribe_u_sftp_f60_000*.log | wc -l`"
  totsubu="${tot}"

  countthem "`grep 'post_log notice' ~/sarra_devdocroot/srpostlogfile.log | wc -l`"
  totpost1="${tot}"

  if [ ! "$C_ALSO" ]; then
     return
  fi

  countthem "`grep 'received:' $LOGDIR/sr_cpump_pelle_dd1_f04_001.log | wc -l`"
  totcpelle04r="${tot}"

  countthem "`grep 'published:' $LOGDIR/sr_cpump_pelle_dd1_f04_001.log | wc -l`"
  totcpelle04p="${tot}"

  countthem "`grep 'received:' $LOGDIR/sr_cpump_pelle_dd2_f05_001.log | wc -l`"
  totcpelle05r="${tot}"

  countthem "`grep 'published:' $LOGDIR/sr_cpump_pelle_dd2_f05_001.log | wc -l`"
  totcpelle05p="${tot}"

  countthem "`grep 'published:' $LOGDIR/sr_cpump_xvan_f14_001.log | wc -l`"
  totcvan14p="${tot}"

  countthem "`grep 'published:' $LOGDIR/sr_cpump_xvan_f15_001.log | wc -l`"
  totcvan15p="${tot}"

  countthem "`grep 'published:' $LOGDIR/sr_cpost_veille_f34_001.log | wc -l`"
  totcveille="${tot}"

  countthem "`grep 'file_log downloaded ' $LOGDIR/sr_subscribe_cdnld_f21_000*.log | wc -l`"
  totcdnld="${tot}"

  countthem "`grep 'file_log downloaded ' $LOGDIR/sr_subscribe_cfile_f44_000*.log | wc -l`"
  totcfile="${tot}"

}

# sr_post initial start
httpdocroot=`cat $tstdir/.httpdocroot`
srpostdir=`cat $tstdir/.httpdocroot`/sent_by_tsource2send
srpostlstfile_new=$httpdocroot/srpostlstfile.new
srpostlstfile_old=$httpdocroot/srpostlstfile.old
srpostlogfile=$httpdocroot/srpostlogfile.log

touch ${srpostlogfile}
echo > ${srpostlstfile_old}


# sr_post call

function do_sr_post {

   cd $srpostdir

   # sr_post testing START
   # TODO - consider if .httpdocroot ends with a '/' ?
   ls $srpostdir > $srpostlstfile_new
   # Obtain file listing delta
   srpostdelta=`comm -23 $srpostlstfile_new $srpostlstfile_old`

   if [ "$srpostdelta" == "" ]; then
      return
   fi

   #sr_post -b amqp://tsource@localhost/ -to ALL -ex xs_tsource_post -u sftp://peter@localhost -dr $srpostdir -p $srpostdelta >> $srpostlogfile 2>&1
   sr_post -c "$CONFDIR"/post/test2_f61.conf  $srpostdelta >> $srpostlogfile 2>&1

   cp -p $srpostlstfile_new $srpostlstfile_old

   do_sr_post

}

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
   countthem "`grep msg_total "$LOGDIR"/sr_report_tsarra_0001.log | tail -1 | awk ' { print $5; }; '`" 
   totsarra="${tot}"
   printf "waiting to start...\n"
done

while [ $totsarra -lt $smin ]; do
   if [ "`sr_shovel t_dd1_f00 status |& tail -1 | awk ' { print $8 } '`" == 'stopped' ]; then 
      echo "starting shovels and waiting..."
      sr_shovel start t_dd1_f00 &
      sr_shovel start t_dd2_f00 
      if [ "${C_ALSO}" ]; then
         sr_cpump start pelle_dd1_f04 &
         sr_cpump start pelle_dd2_f05
      fi
   fi
   sleep 10

   # do sr_posting if requiered
   do_sr_post


   countall

   printf  "sample now %6d \r"  $totsarra

done
printf  "\nSufficient!\n" 

if [ "`sr_shovel t_dd1_f00 status |& tail -1 | awk ' { print $8 } '`" != 'stopped' ]; then 
   echo "stopping shovels and waiting..."
   sr_shovel stop t_dd2_f00 &
   sr_shovel stop t_dd1_f00 
   if [ "${C_ALSO}" ]; then
         sr_cpump stop pelle_dd1_f04 &
         sr_cpump stop pelle_dd2_f05
   fi

   # sleep a little more and then  do sr_posting if requiered
   sleep 10
   do_sr_post

   queued_msgcnt="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv show overview |awk '(NR == 2) { print $3; };'`"
   while [ $queued_msgcnt -gt 0 ]; do
        echo "Still $queued_msgcnt messages flowing, waiting..."
        sleep 10
        queued_msgcnt="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv show overview |awk '(NR == 2) { print $3; };'`"
   done

   ack="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list queues message_stats.ack_details.rate | grep '^[0-9]' | grep -v '^0.0$' | wc -l`"
   inc="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list queues message_stats.incoming_dektails.rate | grep '^[0-9]' | grep -v '^0.0$' | wc -l`"
   del="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list queues message_stats.deliver_dektails.rate | grep '^[0-9]' | grep -v '^0.0$' | wc -l`"
   message_rates=$((ack+inc+del))
   while [ $message_rates -gt 0 ]; do
        echo "Still $message_rates live message rates, waiting..."
        sleep 10
        ack="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list queues message_stats.ack_details.rate | grep '^[0-9]' | grep -v '^0.0$' | wc -l`"
        inc="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list queues message_stats.incoming_dektails.rate | grep '^[0-9]' | grep -v '^0.0$' | wc -l`"
        del="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list queues message_stats.deliver_dektails.rate | grep '^[0-9]' | grep -v '^0.0$' | wc -l`"
        message_rates=$((ack+inc+del))
        ack="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list queues message_stats.ack_details.rate | grep '^[0-9]' | grep -v '^0.0$' | wc -l`"
   done

fi

sleep 10

countall


passedno=0
tno=0

if [ "${totshovel2}" -gt "${totshovel1}" ]; then
   maxshovel=${totshovel2}
else 
   maxshovel=${totshovel1}
fi
printf "\tmaximum of the shovels is: ${maxshovel}\n\n"


calcres "${totshovel1}" "${totshovel2}" "shovels t_dd1_f00 ( ${totshovel1} ) and t_dd2_f00 ( ${totshovel2} ) should have about the same number of items read"  



t2=$(( ${totsarra}*2 ))

calcres ${totwinnow} ${t2} "sarra tsarra ($totsarra) should be reading about half as many items as (both) winnows (${totwinnow})" 

calcres  ${totsarra} ${totfilet} "tsarra (${totsarra}) and sub t_f30 (${totfilet}) should have about the same number of items" 

# this test fails a lot, because it's wrong... if we did it with 3, it would work, but some data has no checksum, so
# there is always more in 00 than in any other.  if we could compare 01 and 02, it would probably work.
#calcres ${totwinnow00} ${totwinnow01} \
#   "winnow00 and (${totwinnow00}) and winnow01 (${totwinnow01}) should have about the same number of items" 

calcres ${maxshovel} ${totfilet} "max shovel (${maxshovel}) and subscriber t_f30 (${totfilet}) should have about the same number of items" 

calcres ${totshortened} ${totfilet} \
   "count of truncated headers (${totshortened}) and subscribed messages (${totmsgt}) should have about the same number of items"

calcres ${totfilet} ${totmsgt} "count of downloads by subscribe t_f30 (${totfilet}) and messages received (${totmsgt}) should be about the same" 

while ! calcres ${totfilet} ${totwatch}  "downloads by subscribe t_f30 (${totfilet}) and files posted by sr_watch (${totwatch}) should be about the same" retry ; do
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

tallyres ${totpoll1} ${totsubq} "poll test1_f62 and subscribe q_f71 run together. Should have equal results."

calcres ${totpost1} ${totsubr} "post test2_f61 ${totpost1} and subscribe r_ftp_f70 ${totsubr} run together. Should be about the same."

# these almost never are the same, and it's a problem with the post test. so failures here almost always false negative.
#calcres ${totpost1} ${totsubu} "post test2_f61 ${totpost1} and subscribe u_sftp_f60 ${totsubu} run together. Should be about the same."

# because of accept/reject filters, these numbers are never similar, so these tests are wrong.
# tallyres ${totcpelle04r} ${totcpelle04p} "pump pelle_dd1_f04 (c shovel) should publish (${totcpelle04p}) as many messages as are received (${totcpelle04r})"
# tallyres ${totcpelle05r} ${totcpelle05p} "pump pelle_dd2_f05 (c shovel) should publish (${totcpelle05p}) as many messages as are received (${totcpelle05r})"

if [ "$C_ALSO" ]; then

  calcres  ${totcpelle04r} ${totcpelle05r} "cpump both pelles (c shovel) should receive about the same number of messages (${totcpelle05r}) (${totcpelle04r})"

  totcvan=$(( ${totcvan14p} + ${totcvan15p} ))
  calcres  ${totcvan} ${totcdnld} "cdnld_f21 subscribe downloaded ($totcdnld) the same number of files that was published by both van_14 and van_15 ($totcvan)"
  calcres  ${totcveille} ${totcdnld} "veille_f34 should post the same number of files ($totcveille) that subscribe cdnld_f21 downloaded ($totcdnld)"
  calcres  ${totcveille} ${totcfile} "veille_f34 should post the same number of files ($totcveille) that subscribe cfile_f44 downloaded ($totcfile)"

fi


calcres ${tno} ${passedno} "Overall ${passedno} of ${tno} passed!"

# MG shows errors in logs if any

echo
NERROR=`grep ERROR "$LOGDIR"/*.log | wc -l`
if ((NERROR>0)); then
   fcel=flow_check_errors_logged.txt
   grep ERROR "$LOGDIR"/*.log | sed 's/:.*ERROR/ \[ERROR/' | uniq -c >$fcel
   result="`wc -l $fcel|cut -d' ' -f1`"
   if [ $result -gt 10 ]; then
       head $fcel
       echo "more than 10 TYPES OF ERRORS found... for the rest, have a look at `pwd`/$fcel for details"
   else
       echo TYPE OF ERRORS IN LOG :
       echo
       cat $fcel
   fi
fi
if ((NERROR==0)); then
   echo NO ERRORS IN LOGS
fi
