#!/bin/bash

# parse arguments
POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -s|--skip_summaries)
    skip_summaries=true
    shift # past argument
    ;;
esac
done
set -- "${POSITIONAL[@]}"

. ./flow_include.sh
countall

function summarize_performance {
    path="$LOGDIR"/$1
    shift
    pattern=$1
    shift
    for i in $* ; do
       best_fn=''
       printf "\n\t$i\n\n"
       for j in ${path}_${i}_*.log*; do
           msg="`grep ${pattern} ${j} | tail -1`"
           if [[ -z "$msg" ]]; then
               continue
           fi
           fn=`echo $(basename ${j}) | awk -F'.' '{print $3}'`
           if [[ -z "$fn" ]]; then
               best_fn=`echo $(basename ${j})`
               echo "`basename $j` ${msg}"
           elif [[ -z "$best_fn" ]]; then
               echo "`basename $j` ${msg}"
           fi
       done
    done
}

function summarize_logs {
    printf "\n$1 Summary:\n"
    input_size=${#1}
    fcl="$LOGDIR"/flowcheck_$1_logged.txt
    msg_counts=`grep -h -o "\[$1\] *.*" "$LOGDIR"/*.log* | sort | uniq -c -w"$((input_size+20))" | sort -n -r`
    echo '' > ${fcl}

    if [[ -z $msg_counts ]]; then
       echo NO $1S IN LOGS
    else
       backup_ifs=$IFS
       IFS=$'\n'
       for msg_line in $msg_counts; do
            count=`echo ${msg_line} | awk '{print $1}'`
            msg=`echo ${msg_line} | sed "s/^ *[0-9]* \[$1\] *//g"`
            pattern="\[$1\] *${msg}"
            filelist=($(grep -l ${pattern::$((input_size + 22))} "$LOGDIR"/*.log*))
            if [[ ${filelist[@]} ]]; then
                first_filename=`basename ${filelist[0]} | sed 's/ /\n/g' | sed 's|.*\/||g' | sed 's/_[0-9][0-9]\.log.*\|.log.*//g' | uniq`
                files_nb=${#filelist[@]}
                echo "  $count%${first_filename}%(${files_nb} file)%`echo ${msg_line} | sed "s/^ *[0-9]* //g"`" >> ${fcl}
                echo ${filelist[@]} | sed 's/^//g' | sed 's/ \//\n\//g' >> ${fcl}
                echo -e >> ${fcl}
            fi
       done
       IFS=${backup_ifs}
       result=`grep -c $1 ${fcl}`
       if [[ ${result} -gt 10 ]]; then
           grep $1 ${fcl} | head | column -t -s % | cut -c -130
           echo
           echo "More than 10 TYPES OF $1S found... for the rest, have a look at $fcl for details"
       else
           grep $1 ${fcl} | column -t -s % | cut -c -130
       fi
    fi
}

if [[ -z "$skip_summaries" ]]; then
    # PAS performance summaries
    printf "\nDownload Performance Summaries:\tLOGDIR=$LOGDIR\n"
    summarize_performance sr_shovel msg_total: t_dd1 t_dd2
    summarize_performance sr_subscribe file_total: cdnld_f21 t_f30 cfile_f44 u_sftp_f60 ftp_f70 q_f71

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

    summarize_logs ERROR
    summarize_logs WARNING
fi

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

  totc04recnrej=$(( ${totcpelle04r} - ${totcpelle04rej} )) 
  calcres  ${totc04recnrej} ${totcpelle04p} "cpump pelle 04 (received - rejected) = published (${totcpelle04r} - ${totcpelle04rej}) = ${totc04recnrej} vs. ${totcpelle04p} "

  totc05recnrej=$(( ${totcpelle05r} - ${totcpelle05rej} )) 
  calcres  ${totc05recnrej} ${totcpelle05p} "cpump pelle 05 (received - rejected) = published (${totcpelle05r} - ${totcpelle05rej}) = ${totc05recnrej} vs. ${totcpelle05p} "

  totcvan=$(( ${totcvan14p} + ${totcvan15p} ))
  calcres  ${totcvan} ${totcdnld} "cdnld_f21 subscribe downloaded ($totcdnld) the same number of files that was published by both van_14 and van_15 ($totcvan)"
  t5=$(( $totcveille / 2 ))
  calcres  ${t5} ${totcdnld} "veille_f34 should post twice as many files ($totcveille) as subscribe cdnld_f21 downloaded ($totcdnld)"
  calcres  ${t5} ${totcfile} "veille_f34 should post twice as many files ($totcveille) as subscribe cfile_f44 downloaded ($totcfile)"

fi

tallyres ${tno} ${passedno} "Overall ${passedno} of ${tno} passed (sample size: $totsarra) !"
results=$?

if (("${missed_dispositions}">0)); then
   # PAS missed_dispositions means definite Sarra bug, very serious.
   echo "Please review $missedreport"
   results=1
fi
echo

exit ${results}
