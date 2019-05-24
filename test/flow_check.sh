#!/bin/bash

. ./flow_include.sh

countall

# PAS performance summaries

printf "\n\n\t\tDownload Performance Summaries:\n\n\tLOGDIR=$LOGDIR"

for i in t_dd1 t_dd2 ;
do
   printf "\n\t$i\n\n"
   #grep 'msg_total' "$LOGDIR"/sr_shovel_${i}_*.log* | sed 's/:/ /' | sort  -k 2,3 | tail -10
   for j in "$LOGDIR"/sr_shovel_${i}_*.log* ; do
       echo "`basename $j` `grep 'msg_total' ${j} | tail -1`"
   done
done

for i in cdnld_f21 t_f30 cfile_f44 u_sftp_f60 ftp_f70 q_f71 ;
do
   printf "\n\t$i\n\n"
   for j in "$LOGDIR"/sr_subscribe_${i}_*.log* ; do
       echo "`basename $j` `grep 'file_total' ${j} | tail -1`"
   done
done

echo
# MG shows retries
echo

if [[ ! "$SARRA_LIB" ]]; then
   echo NB retries for sr_subscribe t_f30 `grep Retrying "$LOGDIR"/sr_subscribe_t_f30*.log* | wc -l`
   echo NB retries for sr_sender    `grep Retrying "$LOGDIR"/sr_sender*.log* | wc -l`
else
   echo NB retries for "$SARRA_LIB"/sr_subscribe.py t_f30 `grep Retrying "$LOGDIR"/sr_subscribe_t_f30*.log* | wc -l`
   echo NB retries for "$SARRA_LIB"/sr_sender.py    `grep Retrying "$LOGDIR"/sr_sender*.log* | wc -l`
fi

function summarizelogs {
    printf "\n$1 Summary:\n\n"
    grep -E -h -o "\[$1\] *[^ ^/][^ ]+ [^/]|\[$1\] *[^ ^/][^ ]+ /|\[$1\] /" "$LOGDIR"/*.log* | sort | uniq -c | sort -r  > "$LOGDIR"/flowcheck_$1count.txt
    NERROR=`grep $1 "$LOGDIR"/flowcheck_$1count.txt | wc -l`

    if (($NERROR>0)); then
       fcel="$LOGDIR"/flow_check_$1s_logged.txt
       while read p; do
            msg_prefix=`echo ${p} | cut -d' ' -f3-`
            filelist=($(grep -l "\[$1\] *$msg_prefix" "$LOGDIR"/*.log*))
            if [[ -z "$filelist" ]]; then
                # Fail proof against an empty string (although the odds are against it) the loop wont stop there
                continue
            fi
            first_filename=`basename ${filelist[0]} | sed 's/ /\n/g' | sed 's|.*\/||g' | sed 's/_[0-9][0-9]\.log\|.log//g' | uniq`
            msg=`grep -o -m 1 "\[$1\] *$msg_prefix.*" ${filelist[0]}`
            files_nb=${#filelist[@]}
            echo "    " "`echo ${p} | awk '{print $1;}'`" "${first_filename}" "(${files_nb} file)" "$msg"
            echo ${filelist[@]} | sed 's/^//g' | sed 's/ \//\n\//g'
            echo -e
       done < "$LOGDIR"/flowcheck_$1count.txt > ${fcel}

       result=`grep -c $1 ${fcel}`
       if [[ ${result} -gt 10 ]]; then
           grep $1 ${fcel} | head | cut -c -130
           echo
           echo "More than 10 TYPES OF $1S found... for the rest, have a look at $fcel for details"
       else
           grep $1 ${fcel} | cut -c -130
       fi
    else
       echo NO $1S IN LOGS
    fi
}
summarizelogs ERROR
summarizelogs WARNING

passedno=0
tno=0

if [[ "${totshovel2}" -gt "${totshovel1}" ]]; then
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
zerowanted "${missed_dispositions}" "${maxshovel}" "messages received that we don't know what happened."
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
results=$?

# PAS missed_dispositions means definite Sarra bug, very serious.

if (("${missed_dispositions}">0)); then
   echo "Please review $missedreport"
   results=1
fi
echo

exit ${results}
