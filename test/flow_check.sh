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

httpdocroot=`cat $tstdir/.httpdocroot`



function countthem {
   if [ ! "${1}" ]; then
      tot=0
   else
      tot="${1}"
   fi
}

function chkargs {

   if [ ! "${1}" -o ! "${2}" ]; then
      printf "test %2d FAILURE: blank results! ${3}\n" ${tno}
      return 2
   fi
   if [ "${1}" -eq 0 ]; then
      printf "test %2d FAILURE: no successful results! ${3}\n" ${tno}
      return 2
   fi

   if [ "${2}" -eq 0 ]; then
      printf "test %2d FAILURE: no successful results, 2nd item! ${3}\n" ${tno}
      return 2
   fi

   return 0
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

   chkargs "${1}" "${2}" "${3}"
   if [ $? -ne 0 ]; then
      return $?
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

function zerowanted {
   # zerowanted - this value must be zero... checking for bad things.
   # 
   # logic:
   # increment test number (tno)
   # compare first and second totals, and report agreement if within 10% of one another.
   # emit description based on agreement.  Arguments:
   # 1 - value obtained 
   # 2 - test description string.

   tno=$((${tno}+1))

   if [ "${1}" -gt 0 ]; then
      printf "test %2d FAILURE: ${1} ${2}\n" ${tno}
   else
      printf "test %2d success: ${1} ${2}\n" ${tno}
      passedno=$((${passedno}+1))
   fi
}

function sumlogs {

  pat="$1"
  shift
  tot=0
  for l in $*; do
     to_add="`grep $pat $l | tail -1 | awk ' { print $5; }; '`"
     if [ "$to_add" ]; then
          tot=$((${tot}+${to_add}))
     fi
  done
}

function countall {

  sumlogs msg_total $LOGDIR/sr_report_tsarra_f20_000*.log 
  totsarra="${tot}"

  sumlogs msg_total $LOGDIR/sr_report_twinnow00_f10_000*.log 
  totwinnow00="${tot}"

  countthem "`grep msg_total "$LOGDIR"/sr_report_twinnow01_f10_0001.log | tail -1 | awk ' { print $5; }; '`"
  sumlogs msg_total $LOGDIR/sr_report_twinnow01_f10_000*.log 
  totwinnow01="${tot}"

  totwinnow=$(( ${totwinnow00} + ${totwinnow01} ))

  sumlogs msg_total $LOGDIR/sr_subscribe_t_f30_000*.log
  totmsgt="${tot}"

  sumlogs file_total $LOGDIR/sr_subscribe_t_f30_000*.log
  totfilet="${tot}"

  sumlogs msg_total $LOGDIR/sr_shovel_t_dd1_f00_000*.log
  totshovel1="${tot}"

  sumlogs msg_total $LOGDIR/sr_shovel_t_dd2_f00_000*.log
  totshovel2="${tot}"

  sumlogs post_total $LOGDIR/sr_watch_f40_000*.log
  totwatch="${tot}"

  countthem "`grep truncating "$LOGDIR"/sr_sarra_download_f20_000*.log | wc -l`"
  totshortened="${tot}"

  countthem "`grep post_log "$LOGDIR"/sr_sender_tsource2send_f50_000*.log | wc -l`"
  totsent="${tot}"

  countthem "`grep 'downloaded to:' "$LOGDIR"/sr_subscribe_q_f71_000*.log | wc -l`"
  totsubq="${tot}"
  countthem  "`grep 'post_log notice' "$LOGDIR"/sr_poll_f62_000*.log | wc -l`"
  totpoll1="${tot}"

  countthem "`grep 'downloaded to:' "$LOGDIR"/sr_subscribe_ftp_f70_000*.log | wc -l`"
  totsubr="${tot}"

  countthem "`grep 'downloaded to:' "$LOGDIR"/sr_subscribe_u_sftp_f60_000*.log | wc -l`"
  totsubu="${tot}"

  countthem "`grep 'post_log notice' $LOGDIR/srposter.log | wc -l`"
  totpost1="${tot}"

  countthem "`grep 'published: 2' $LOGDIR/srposter.log | wc -l`"
  totshimpost1="${tot}"

  if [ ! "$C_ALSO" ]; then
     return
  fi

  countthem "`grep 'received:' $LOGDIR/sr_cpump_pelle_dd1_f04_0001.log | wc -l`"
  totcpelle04r="${tot}"

  countthem "`grep 'published:' $LOGDIR/sr_cpump_pelle_dd1_f04_0001.log | wc -l`"
  totcpelle04p="${tot}"

  countthem "`grep 'received:' $LOGDIR/sr_cpump_pelle_dd2_f05_0001.log | wc -l`"
  totcpelle05r="${tot}"

  countthem "`grep 'published:' $LOGDIR/sr_cpump_pelle_dd2_f05_0001.log | wc -l`"
  totcpelle05p="${tot}"

  countthem "`grep 'published:' $LOGDIR/sr_cpump_xvan_f14_0001.log | wc -l`"
  totcvan14p="${tot}"

  countthem "`grep 'published:' $LOGDIR/sr_cpump_xvan_f15_0001.log | wc -l`"
  totcvan15p="${tot}"

  countthem "`grep 'published:' $LOGDIR/sr_cpost_veille_f34_0001.log | wc -l`"
  totcveille="${tot}"

  countthem "`grep 'file_log downloaded ' $LOGDIR/sr_subscribe_cdnld_f21_000*.log | wc -l`"
  totcdnld="${tot}"

  countthem "`grep 'file_log downloaded ' $LOGDIR/sr_subscribe_cfile_f44_000*.log | wc -l`"
  totcfile="${tot}"

  audit_state="`grep 'INFO\].*msg_auditflow' $LOGDIR/sr_subscribe_clean_f90_0001.log | tail -1 | awk ' { print $5; };'`"
  audit_t1="`grep 'INFO\].*msg_auditflow' $LOGDIR/sr_subscribe_clean_f90_0001.log | tail -1 | awk ' { print $12; };'`"
  audit_t2="`grep 'INFO\].*msg_auditflow' $LOGDIR/sr_subscribe_clean_f90_0002.log | tail -1 | awk ' { print $12; };'`"
  audit_t3="`grep 'INFO\].*msg_auditflow' $LOGDIR/sr_subscribe_clean_f90_0003.log | tail -1 | awk ' { print $12; };'`"
  audit_t4="`grep 'INFO\].*msg_auditflow' $LOGDIR/sr_subscribe_clean_f90_0004.log | tail -1 | awk ' { print $12; };'`"
  audit_t5="`grep 'INFO\].*msg_auditflow' $LOGDIR/sr_subscribe_clean_f90_0005.log | tail -1 | awk ' { print $12; };'`"

  # flags when two lines include *msg_log received* (with no other message between them) indicating no user will know what happenned.
  awk 'BEGIN { lr=0; }; /msg_log received/ { lr++; print lr, FILENAME, $0 ; next; }; { lr=0; } '  $LOGDIR/sr_subscribe_*_000*.log  | grep -v '^1 ' >$LOGDIR/missed_dispositions.report
  missed_dispositions="`wc -l <$LOGDIR/missed_dispositions.report`"

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
   countthem "`grep msg_total "$LOGDIR"/sr_report_tsarra_f20_0001.log | tail -1 | awk ' { print $5; }; '`" 
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

   countall

   printf  "sample now %6d content_checks:%4s missed_dispositions:%d\r"  "$totsarra" "$audit_state" "$missed_dispositions"

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

   sleep 10

   queued_msgcnt="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv show overview |awk '(NR == 2) { print $3; };'`"
   while [ $queued_msgcnt -gt 0 ]; do
        printf "Still %4s messages flowing, waiting...\r" "$queued_msgcnt"
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

#sleep 10

countall


passedno=0
tno=0

if [ "${totshovel2}" -gt "${totshovel1}" ]; then
   maxshovel=${totshovel2}
else 
   maxshovel=${totshovel1}
fi
printf "\tmaximum of the shovels is: ${maxshovel}\n\n"


calcres "${totshovel1}" "${totshovel2}" "shovels t_dd1_f00 (${totshovel1}) and t_dd2_f00 (${totshovel2}) should have about the same number of items read"  



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

t3=$(( ${totfilet}*2 ))

while ! calcres ${t3} ${totwatch}  "same downloads by subscribe t_f30 (${t3}) and files posted (add+remove) by sr_watch (${totwatch}) should be about the same" retry ; do
    printf "info: retrying... waiting for totwatch to catchup\n"
    sleep 5
    oldtotwatch=${totwatch}
    countall
    t3=$(( ${totfilet}*2 ))
    if [ "${oldtotwatch}" -eq "${totwatch}"  ]; then
       printf "error: giving up on this test\n"
       tno=$((${tno}+1))
       break
    fi
done

calcres ${totwatch} ${totsent} "posted by watch(${totwatch}) and sent by sr_sender (${totsent}) should be about the same"

zerowanted "${missed_dispositions}" "messages received that we don't know what happenned."
calcres "${audit_t1}" "${audit_t2}" "comparing audit file totals, instances 1 (${audit_t1}) and 2 (${audit_t2}) should be about the same."
calcres "${audit_t2}" "${audit_t3}" "comparing audit file totals, instances 2 (${audit_t2}) and 3 (${audit_t3}) should be about the same."
calcres "${audit_t3}" "${audit_t4}" "comparing audit file totals, instances 3 (${audit_t3}) and 4 (${audit_t4}) should be about the same."
calcres "${audit_t4}" "${audit_t5}" "comparing audit file totals, instances 4 (${audit_t4}) and 5 (${audit_t5}) should be about the same."

calcres ${totpoll1} ${totsubq} "poll test1_f62 and subscribe q_f71 run together. Should have equal results."

calcres ${totpost1} ${totsubr} "post test2_f61 ${totpost1} and subscribe r_ftp_f70 ${totsubr} run together. Should be about the same."

calcres ${totpost1} ${totshimpost1} "posts test2_f61 ${totpost1} and shim_f63 ${totshimpost1} Should be the same."


# these almost never are the same, and it's a problem with the post test. so failures here almost always false negative.
#calcres ${totpost1} ${totsubu} "post test2_f61 ${totpost1} and subscribe u_sftp_f60 ${totsubu} run together. Should be about the same."

# because of accept/reject filters, these numbers are never similar, so these tests are wrong.
# tallyres ${totcpelle04r} ${totcpelle04p} "pump pelle_dd1_f04 (c shovel) should publish (${totcpelle04p}) as many messages as are received (${totcpelle04r})"
# tallyres ${totcpelle05r} ${totcpelle05p} "pump pelle_dd2_f05 (c shovel) should publish (${totcpelle05p}) as many messages as are received (${totcpelle05r})"

if [ "$C_ALSO" ]; then

  calcres  ${totcpelle04r} ${totcpelle05r} "cpump both pelles (c shovel) should receive about the same number of messages (${totcpelle05r}) (${totcpelle04r})"

  totcvan=$(( ${totcvan14p} + ${totcvan15p} ))
  calcres  ${totcvan} ${totcdnld} "cdnld_f21 subscribe downloaded ($totcdnld) the same number of files that was published by both van_14 and van_15 ($totcvan)"
  t5=$(( $totcveille / 2 ))
  calcres  ${t5} ${totcdnld} "veille_f34 should post twice as many files ($totcveille) as subscribe cdnld_f21 downloaded ($totcdnld)"
  calcres  ${t5} ${totcfile} "veille_f34 should post twice as many files ($totcveille) as subscribe cfile_f44 downloaded ($totcfile)"

fi


calcres ${tno} ${passedno} "Overall ${passedno} of ${tno} passed (sample size: $totsarra) !"

# MG shows retries

echo
echo NB retries for sr_subscribe t_f30 `grep Retrying "$LOGDIR"/sr_subscribe_t_f30*.log | wc -l`
echo NB retries for sr_sender    `grep Retrying "$LOGDIR"/sr_sender*.log | wc -l`

# MG shows errors in logs if any

if (("${missed_dispositions}">0)); then 
   echo "Please review $LOGDIR/missed_dispositions.report" 
fi

echo
NERROR=`grep ERROR "$LOGDIR"/*.log | grep -v ftps | grep -v retryhost | wc -l`
if ((NERROR>0)); then
   fcel=flow_check_errors_logged.txt
   grep ERROR "$LOGDIR"/*.log | grep -v ftps | grep -v retryhost | sed 's/:.*ERROR/ \[ERROR/' | uniq -c >$fcel
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

