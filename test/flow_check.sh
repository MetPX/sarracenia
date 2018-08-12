#!/bin/bash

if [[ ":$SARRA_LIB/../:" != *":$PYTHONPATH:"* ]]; then
    if [ "${PYTHONPATH:${#PYTHONPATH}-1}" == ":" ]; then
        export PYTHONPATH="$PYTHONPATH$SARRA_LIB/../"
    else 
        export PYTHONPATH="$PYTHONPATH:$SARRA_LIB/../"
    fi
fi

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

  sumlogs msg_total $LOGDIR/sr_report_tsarra_f20_*.log
  totsarra="${tot}"

  sumlogs msg_total $LOGDIR/sr_report_twinnow00_f10_*.log
  totwinnow00="${tot}"

  sumlogs msg_total $LOGDIR/sr_report_twinnow01_f10_*.log 
  totwinnow01="${tot}"

  totwinnow=$(( ${totwinnow00} + ${totwinnow01} ))

  sumlogs msg_total $LOGDIR/sr_shovel_t_dd1_f00_*.log
  totshovel1="${tot}"

  sumlogs msg_total $LOGDIR/sr_shovel_t_dd2_f00_*.log
  totshovel2="${tot}"

  countthem "`grep post_log "$LOGDIR"/sr_winnow*.log* | wc -l`"
  totwinpost="${tot}"

  countthem "`grep truncating "$LOGDIR"/sr_sarra_download_f20_*.log* | wc -l`"
  totshortened="${tot}"

  sumlogs post_total $LOGDIR/sr_watch_f40_*.log
  totwatch="${tot}"

  sumlogs msg_total $LOGDIR/sr_subscribe_t_f30_*.log
  totmsgt="${tot}"

  sumlogs file_total $LOGDIR/sr_subscribe_t_f30_*.log
  totfilet="${tot}"

  countthem "`grep post_log "$LOGDIR"/sr_sender_tsource2send_f50_*.log* | wc -l`"
  totsent="${tot}"

  countthem "`grep 'downloaded to:' "$LOGDIR"/sr_subscribe_u_sftp_f60_*.log* | wc -l`"
  totsubu="${tot}"
  countthem "`grep 'hardlink' "$LOGDIR"/sr_subscribe_u_sftp_f60_*.log* | wc -l`"
  totsubu=$(( totsubu + tot ))
  countthem "`grep 'symlinked to' "$LOGDIR"/sr_subscribe_u_sftp_f60_*.log* | wc -l`"
  totsubu=$(( totsubu + tot ))
  countthem "`grep 'removed' "$LOGDIR"/sr_subscribe_u_sftp_f60_*.log* | wc -l`"
  totsubu=$(( totsubu + tot ))

  countthem "`grep 'downloaded to:' "$LOGDIR"/sr_subscribe_q_f71_*.log* | wc -l`"
  totsubq="${tot}"
  countthem "`grep 'symlinked to' "$LOGDIR"/sr_subscribe_q_f71_*.log* | wc -l`"
  totsubq=$(( totsubq + tot ))
  countthem "`grep 'removed' "$LOGDIR"/sr_subscribe_q_f71_*.log* | wc -l`"
  totsubq=$(( totsubq + tot ))

  countthem  "`grep 'post_log notice' "$LOGDIR"/sr_poll_f62_*.log* | wc -l`"
  totpoll1="${tot}"

  countthem "`grep 'downloaded to:' "$LOGDIR"/sr_subscribe_ftp_f70_*.log* | wc -l`"
  totsubftp="${tot}"
  countthem "`grep 'symlinked to' "$LOGDIR"/sr_subscribe_ftp_f70_*.log* | wc -l`"
  totsubftp=$(( totsubftp + tot ))
  countthem "`grep 'removed' "$LOGDIR"/sr_subscribe_ftp_f70_*.log* | wc -l`"
  totsubftp=$(( totsubftp + tot ))

  countthem "`grep 'downloaded to:' "$LOGDIR"/sr_subscribe_cp_f61_*.log* | wc -l`"
  totsubcp="${tot}"
  countthem "`grep 'hardlink' "$LOGDIR"/sr_subscribe_cp_f61_*.log* | wc -l`"
  totsubcp=$(( totsubcp + tot ))
  countthem "`grep 'symlinked to' "$LOGDIR"/sr_subscribe_cp_f61_*.log* | wc -l`"
  totsubcp=$(( totsubcp + tot ))
  countthem "`grep 'removed' "$LOGDIR"/sr_subscribe_cp_f61_*.log* | wc -l`"
  totsubcp=$(( totsubcp + tot ))

  countthem "`grep 'post_log notice' $LOGDIR/srposter.log | grep -v shim | wc -l`"
  totpost1="${tot}"

  countthem "`grep 'published:' $LOGDIR/srposter.log | grep shim | wc -l`"
  totshimpost1="${tot}"

  countthem "`grep post_log "$LOGDIR"/sr_sarra_download_f20_*.log* | wc -l`"
  totsarp="${tot}"

  if [[ ! "$C_ALSO" && ! -d "$SARRAC_LIB" ]]; then
     return
  fi

  countthem "`grep 'received:' $LOGDIR/sr_cpump_pelle_dd1_f04_*.log* | wc -l`"
  totcpelle04r="${tot}"

  countthem "`grep 'published:' $LOGDIR/sr_cpump_pelle_dd1_f04_*.log* | wc -l`"
  totcpelle04p="${tot}"

  countthem "`grep 'received:' $LOGDIR/sr_cpump_pelle_dd2_f05_*.log* | wc -l`"
  totcpelle05r="${tot}"

  countthem "`grep 'published:' $LOGDIR/sr_cpump_pelle_dd2_f05_*.log* | wc -l`"
  totcpelle05p="${tot}"

  countthem "`grep 'published:' $LOGDIR/sr_cpump_xvan_f14_*.log* | wc -l`"
  totcvan14p="${tot}"

  countthem "`grep 'published:' $LOGDIR/sr_cpump_xvan_f15_*.log* | wc -l`"
  totcvan15p="${tot}"

  countthem "`grep 'published:' $LOGDIR/sr_cpost_veille_f34_*.log* | wc -l`"
  totcveille="${tot}"

  countthem "`grep 'file_log downloaded ' $LOGDIR/sr_subscribe_cdnld_f21_*.log* | wc -l`"
  totcdnld="${tot}"

  countthem "`grep 'file_log downloaded ' $LOGDIR/sr_subscribe_cfile_f44_*.log* | wc -l`"
  totcfile="${tot}"

  sumlogs post_total $LOGDIR/sr_shovel_pclean_f90*.log
  totpropagated="${tot}"

  sumlogs post_total $LOGDIR/sr_shovel_pclean_f92*.log
  totremoved="${tot}"

  # flags when two lines include *msg_log received* (with no other message between them) indicating no user will know what happenned.

  # flags when two lines include *msg_log received* (with no other message between them) indicating no user will know what happenned.
  awk 'BEGIN { lr=0; }; /msg_log received/ { lr++; print lr, FILENAME, $0 ; next; }; { lr=0; } '  $LOGDIR/sr_subscribe_*_0*.log*  | grep -v '^1 ' >$LOGDIR/missed_dispositions.report
  missed_dispositions="`wc -l <$LOGDIR/missed_dispositions.report`"

}


countall

snum=1

if [ "$1" ]; then
   smin=$1
else
   smin=1000
fi

printf "Initial sample building sample size $totsarra need at least $smin \n"

while [ "${totsarra}" == 0 ]; do
   sleep 10
   countthem "`grep msg_total "$LOGDIR"/sr_report_tsarra_f20_01.log | tail -1 | awk ' { print $5; }; '`" 
   totsarra="${tot}"
   printf "Waiting to start...\n"
done

while [ $totsarra -lt $smin ]; do

    if [ ! "$SARRA_LIB" ]; then

       if [ "`sr_shovel t_dd1_f00 status |& tail -1 | awk ' { print $8 } '`" == 'stopped' ]; then 
          echo "Starting shovels and waiting..."
          sr_shovel start t_dd1_f00 &
          sr_shovel start t_dd2_f00
          if [ "$SARRAC_LIB" ]; then
             "$SARRAC_LIB"/sr_cpump start pelle_dd1_f04 &
             "$SARRAC_LIB"/sr_cpump start pelle_dd2_f05             
          elif [ "${C_ALSO}" ]; then
             sr_cpump start pelle_dd1_f04 &
             sr_cpump start pelle_dd2_f05
          fi
       fi
   else
       
       if [ "`"$SARRA_LIB"/sr_shovel.py t_dd1_f00 status |& tail -1 | awk ' { print $8 } '`" == 'stopped' ]; then 
          echo "Starting shovels and waiting..."
          "$SARRA_LIB"/sr_shovel.py start t_dd1_f00 &
          "$SARRA_LIB"/sr_shovel.py start t_dd2_f00 
          if [ "$SARRAC_LIB" ]; then
             "$SARRAC_LIB"/sr_cpump start pelle_dd1_f04 &
             "$SARRAC_LIB"/sr_cpump start pelle_dd2_f05  
          elif [ "${C_ALSO}" ]; then
             sr_cpump start pelle_dd1_f04 &
             sr_cpump start pelle_dd2_f05
          fi  
       fi
   fi
 
   sleep 10
   countall

   printf  "Sample now: %6d Missed_dispositions:%d\r"  "$totsarra" "$missed_dispositions"

done
printf  "\nSufficient!\n" 

# if msg_stopper plugin is used this should not happen
if [ ! "$SARRA_LIB" ]; then
   if [ "`sr_shovel t_dd1_f00 status |& tail -1 | awk ' { print $8 } '`" != 'stopped' ]; then 
       echo "Stopping shovels and waiting..."
       sr_shovel stop t_dd2_f00 &
       sr_shovel stop t_dd1_f00 
   fi
else 
   if [ "`$SARRA_LIB/sr_shovel.py t_dd1_f00 status |& tail -1 | awk ' { print $8 } '`" != 'stopped' ]; then
       echo "Stopping shovels and waiting..."
       "$SARRA_LIB"/sr_shovel.py stop t_dd2_f00 &
       "$SARRA_LIB"/sr_shovel.py stop t_dd1_f00
   fi
fi

if [ "$SARRAC_LIB" ]; then
   "$SARRAC_LIB"/sr_cpump stop pelle_dd1_f04 &
   "$SARRAC_LIB"/sr_cpump stop pelle_dd2_f05
elif [ "${C_ALSO}" ]; then
   sr_cpump stop pelle_dd1_f04 &
   sr_cpump stop pelle_dd2_f05
fi

sleep 10

if [ ! "$SARRA_LIB" ]; then
    cmd="`sr_shovel t_dd1_f00 status |& tail -1 | awk ' { print $8 } '`"
else
    cmd="`"$SARRA_LIB"/sr_shovel.py t_dd1_f00 status |& tail -1 | awk ' { print $8 } '`"
fi

if [ $cmd == 'stopped' ]; then 

   stalled=0
   stalled_value=-1
   retry_msgcnt="`cat "$CACHEDIR"/*/*/*retry* 2>/dev/null | wc -l`"
   ((retry_msgcnt=retry_msgcnt/3))
   while [ $retry_msgcnt -gt 0 ]; do
        printf "Still %4s messages to retry, waiting...\r" "$retry_msgcnt"
        sleep 10
        retry_msgcnt="`cat "$CACHEDIR"/*/*/*retry* 2> /dev/null | wc -l`"
        ((retry_msgcnt=retry_msgcnt/3))

        if [ "${stalled_value}" == "${retry_msgcnt}" ]; then
              stalled=$((stalled+1));
              if [ "${stalled}" == 5 ]; then
                 printf "\n    Warning some retries stalled, skipping..., might want to check the logs\n\n"
                 retry_msgcnt=0
              fi
        else
              stalled_value=$retry_msgcnt
              stalled=0
        fi

   done

   #queued_msgcnt="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list queues | awk ' BEGIN {t=0;} (NR > 1)  && /_f[0-9][0-9]/ { t+=$(23); }; END { print t; };'`"
   queued_msgcnt="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list queues | awk ' BEGIN {t=0;} (NR > 1)  && /_f[0-9][0-9]/ { t+=$2; }; END { print t; };'`"
   while [ $queued_msgcnt -gt 0 ]; do
        printf "Still %4s messages flowing, waiting...\r" "$queued_msgcnt"
        sleep 10
        queued_msgcnt="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list queues | awk ' BEGIN {t=0;} (NR > 1)  && /_f[0-9][0-9]/ { t+=$2; }; END { print t; };'`"
   done
   echo "No messages left in queues..."

echo "FIXME: skipping rabbitmqadmin rate stuff that doesn´t work at all... need some plugin, but no idea which"
# 2018 - following stuff does not work on m
#   ack="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list queues message_stats.ack_details.rate | grep '^[0-9]' | grep -v '^0.0$' | wc -l`"
#   inc="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list queues message_stats.incoming_details.rate | grep '^[0-9]' | grep -v '^0.0$' | wc -l`"
#   del="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list queues message_stats.deliver_details.rate | grep '^[0-9]' | grep -v '^0.0$' | wc -l`"
# 
#   if [ "$ack" -a "$inc" -a "$del" ]; then
#       message_rates=$((ack+inc+del))
#       while [ $message_rates -gt 0 ]; do
#            echo "Still $message_rates live message rates, waiting..."
#            sleep 10
#            ack="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list queues message_stats.ack_details.rate | grep '^[0-9]' | grep -v '^0.0$' | wc -l`"
#            inc="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list queues message_stats.incoming_details.rate | grep '^[0-9]' | grep -v '^0.0$' | wc -l`"
#            del="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list queues message_stats.deliver_details.rate | grep '^[0-9]' | grep -v '^0.0$' | wc -l`"
#            message_rates=$((ack+inc+del))
#            ack="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list queues message_stats.ack_details.rate | grep '^[0-9]' | grep -v '^0.0$' | wc -l`"
#       done
#   fi
fi

#sleep 60

countall

# MG shows retries

echo
if [ ! "$SARRA_LIB" ]; then
   echo NB retries for sr_subscribe t_f30 `grep Retrying "$LOGDIR"/sr_subscribe_t_f30*.log* | wc -l`
   echo NB retries for sr_sender    `grep Retrying "$LOGDIR"/sr_sender*.log* | wc -l`
else
   echo NB retries for "$SARRA_LIB"/sr_subscribe.py t_f30 `grep Retrying "$LOGDIR"/sr_subscribe_t_f30*.log* | wc -l`
   echo NB retries for "$SARRA_LIB"/sr_sender.py    `grep Retrying "$LOGDIR"/sr_sender*.log* | wc -l`
fi


printf "ERROR Sumary:\n\n"

NERROR=`grep ERROR "$LOGDIR"/*.log* | grep -v ftps | grep -v retryhost | wc -l`
if ((NERROR>0)); then
   fcel=$LOGDIR/flow_check_errors_logged.txt
   grep ERROR "$LOGDIR"/*.log* | grep -v ftps | grep -v retryhost | sed 's/:.*ERROR/ \[ERROR/' | uniq -c >$fcel
   result="`wc -l $fcel|cut -d' ' -f1`"
   if [ $result -gt 10 ]; then
       head $fcel
       echo
       echo "More than 10 TYPES OF ERRORS found... for the rest, have a look at $fcel for details"
   else
       echo TYPE OF ERRORS IN LOG :
       echo
       cat $fcel
   fi
fi

if ((NERROR==0)); then
   echo NO ERRORS IN LOGS
fi

printf "WARNING Sumary:\n\n"

NWARNING=`grep WARNING "$LOGDIR"/*.log* | grep -v ftps | grep -v retryhost | wc -l`
if ((NWARNING>0)); then
   fcwl=$LOGDIR/flow_check_warnings_logged.txt
   grep WARNING "$LOGDIR"/*.log* | grep -v ftps | grep -v retryhost | sed 's/:.*WARNING/ \[WARNING/' | uniq -c >$fcwl
   result="`wc -l $fcwl|cut -d' ' -f1`"
   if [ $result -gt 10 ]; then
       head $fcwl
       echo
       echo "More than 10 TYPES OF WARNINGS found... for the rest, have a look at $fcwl for details"
   else
       echo TYPE OF WARNINGS IN LOG :
       echo
       cat $fcwl
   fi
fi
if ((NWARNING==0)); then
   echo NO WARNINGS IN LOGS
fi


passedno=0
tno=0

if [ "${totshovel2}" -gt "${totshovel1}" ]; then
   maxshovel=${totshovel2}
else 
   maxshovel=${totshovel1}
fi
printf "\n\tMaximum of the shovels is: ${maxshovel}\n\n"

printf "\t\tTEST RESULTS\n\n"

tot2shov=$(( ${totshovel1} + ${totshovel2} ))
t4=$(( ${totfilet}*4 ))
t5=$(( ${totsent}/2 ))

echo "                 | dd.weather routing |"
calcres ${totshovel1} ${totshovel2} "sr_shovel\t (${totshovel1}) t_dd1 should have the same number of items as t_dd2\t (${totshovel2})"
calcres ${totwinnow}  ${tot2shov}   "sr_winnow\t (${totwinnow}) should have the same of the number of items of shovels\t (${tot2shov})"
calcres ${totsarp}    ${totwinpost} "sr_sarra\t (${totsarp}) should have the same number of items as winnows'post\t (${totwinpost})"
calcres ${totfilet}   ${totsarp}    "sr_subscribe\t (${totfilet}) should have the same number of items as sarra\t\t (${totsarp})"
echo "                 | watch      routing |"
calcres ${totwatch}   ${t4}         "sr_watch\t\t (${totwatch}) should be 4 times subscribe t_f30\t\t  (${totfilet})"
calcres ${totsent}    ${totwatch}   "sr_sender\t\t (${totsent}) should have the same number of items as sr_watch  (${totwatch})"
calcres ${totsubu}    ${totsent}    "sr_subscribe u_sftp_f60 (${totsubu}) should have the same number of items as sr_sender (${totsent})"
calcres ${totsubcp}   ${totsent}    "sr_subscribe cp_f61\t (${totsubcp}) should have the same number of items as sr_sender (${totsent})"
echo "                 | poll       routing |"
calcres ${totpoll1}   ${t5}         "sr_poll test1_f62\t (${totpoll1}) should have half the same number of items of sr_sender\t (${totsent})"
calcres ${totsubq}    ${totpoll1}   "sr_subscribe q_f71\t (${totsubq}) should have the same number of items as sr_poll test1_f62 (${totpoll1})"
echo "                 | flow_post  routing |"
calcres ${totpost1}   ${t5}         "sr_post test2_f61\t (${totpost1}) should have half the same number of items of sr_sender \t (${totsent})"
calcres ${totsubftp}  ${totpost1}   "sr_subscribe ftp_f70\t (${totsubftp}) should have the same number of items as sr_post test2_f61 (${totpost1})"
calcres ${totpost1} ${totshimpost1} "sr_post test2_f61\t (${totpost1}) should have about the same number of items as shim_f63\t (${totshimpost1})"

echo "                 | py infos   routing |"
calcres ${totpropagated} ${totwinpost} "sr_shovel pclean_f90 (${totpropagated}) should have the same number of watched items winnows' post\t (${totwinpost})"
calcres ${totremoved}    ${totwinpost} "sr_shovel pclean_f92 (${totremoved}) should have the same number of removed items winnows' post\t (${totwinpost})"
zerowanted "${missed_dispositions}" "messages received that we don't know what happened."
calcres ${totshortened} ${totfilet} \
   "count of truncated headers (${totshortened}) and subscribed messages (${totmsgt}) should have about the same number of items"

# these almost never are the same, and it's a problem with the post test. so failures here almost always false negative.
#calcres ${totpost1} ${totsubu} "post test2_f61 ${totpost1} and subscribe u_sftp_f60 ${totsubu} run together. Should be about the same."

# because of accept/reject filters, these numbers are never similar, so these tests are wrong.
# tallyres ${totcpelle04r} ${totcpelle04p} "pump pelle_dd1_f04 (c shovel) should publish (${totcpelle04p}) as many messages as are received (${totcpelle04r})"
# tallyres ${totcpelle05r} ${totcpelle05p} "pump pelle_dd2_f05 (c shovel) should publish (${totcpelle05p}) as many messages as are received (${totcpelle05r})"

if [[ "$C_ALSO" || -d "$SARRAC_LIB" ]]; then

echo "                 | C          routing |"
  calcres  ${totcpelle04r} ${totcpelle05r} "cpump both pelles (c shovel) should receive about the same number of messages (${totcpelle05r}) (${totcpelle04r})"

  totcvan=$(( ${totcvan14p} + ${totcvan15p} ))
  calcres  ${totcvan} ${totcdnld} "cdnld_f21 subscribe downloaded ($totcdnld) the same number of files that was published by both van_14 and van_15 ($totcvan)"
  t5=$(( $totcveille / 2 ))
  calcres  ${t5} ${totcdnld} "veille_f34 should post twice as many files ($totcveille) as subscribe cdnld_f21 downloaded ($totcdnld)"
  calcres  ${t5} ${totcfile} "veille_f34 should post twice as many files ($totcveille) as subscribe cfile_f44 downloaded ($totcfile)"

fi


calcres ${tno} ${passedno} "Overall ${passedno} of ${tno} passed (sample size: $totsarra) !"

# PAS missed_dispositions means definite Sarra bug, very serious.

if (("${missed_dispositions}">0)); then 
   echo "Please review $LOGDIR/missed_dispositions.report" 
fi

echo

