#!/usr/bin/env bash


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

function sr_action {
    msg=$1
    action=$2
    options=$3
    logpipe=$4
    files=$5

    echo $msg
    if [ "$SARRAC_LIB" ]; then
      echo $files | sed 's/ / ; sr_/g' | sed 's/$/ ;/' | sed 's/^/ sr_/' | sed "s+/+ $action +g" | grep -Po "sr_c[\w]* $action [\w\_\. ]* ;" | sed 's~^~"$SARRAC_LIB"/~' | sh
    else
      echo $files | sed 's/ / ; sr_/g' | sed 's/$/ ;/' | sed 's/^/ sr_/' | sed "s+/+ $action +g" |
      sed "s+ ;+ $logpipe ;+g" | grep -Po "sr_c[\w]* $action [\w\_\. ]* $logpipe ;" | sed 's/ \{2,\}/ /g' | sh
    fi
    if [ "$SARRA_LIB" ]; then
      echo $files | sed 's/ / ; sr_/g' | sed 's/$/ ;/' | sed 's/^/ sr_/' | sed "s+/+ $action +g" | grep -Po "sr_[^c][\w]* $action [\w\_\. ]* ;" | sed 's/ /.py /' | sed 's~^~"$SARRA_LIB"/~' | sh
    else
      echo $files | sed 's/ / ; sr_/g' | sed 's/$/ ;/' | sed 's/^/ sr_/' | sed "s+/+ $options $action +g" | sed "s+ ;+ $logpipe ;+g" | grep -Po "sr_[^c][\w]* $options $action [\w\_\. ]* $logpipe ;" | sed 's/ \{2,\}/ /g' | sh
    fi
}

function qchk {
    #
    # qchk verify correct number of queues present.
    #
    # 1 - number of queues to expect.
    # 2 - Description string.
    # 3 - query
    #
    queue_cnt="`rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list queues | awk ' BEGIN {t=0;} (NR > 1)  && /_f[0-9][0-9]/ { t+=1; }; END { print t; };'`"

    if [ "$queue_cnt" = $1 ]; then
        echo "OK, as expected $1 $2"
        passed_checks=$((${passed_checks}+1))
    else
        echo "FAILED, expected $1, but there are $queue_cnt $2"
    fi

    count_of_checks=$((${count_of_checks}+1))

}

function xchk {
    #
    # qchk verify correct number of exchanges present.
    #
    # 1 - number of exchanges to expect.
    # 2 - Description string.
    #
    exex=flow_lists/exchanges_expected.txt
    rabbitmqadmin -H localhost -u bunnymaster -p ${adminpw} -f tsv list exchanges | grep -v '^name' | grep -v amq\. | grep -v rabbitmqtt | grep -v direct| sort >$exnow

    x_cnt="`wc -l <$exnow`"
    expected_cnt="`wc -l <$exex`"

    if [ "$x_cnt" -ge $expected_cnt ]; then
        echo "OK, as expected $expected_cnt $1"
        passed_checks=$((${passed_checks}+1))
    else
        echo "FAILED, expected $expected_cnt, but there are $x_cnt $1"
        printf "Missing exchanges: %s\n" "`comm -23 $exex $exnow`"
    fi
    if [ "$x_cnt" -gt $expected_cnt ]; then
        printf "NOTE: Extra exchanges: %s\n" "`comm -13 $exex $exnow`"
    fi

    count_of_checks=$((${count_of_checks}+1))

}


# Code execution shared by more than 1 flow test script

#FIXME: puts the path at the end? so if you have multiple, guaranteed to take the wrong one?
#       psilva worry 2019/01
#
if [[ ":$SARRA_LIB/../:" != *":$PYTHONPATH:"* ]]; then
    if [ "${PYTHONPATH:${#PYTHONPATH}-1}" == ":" ]; then
        export PYTHONPATH="$PYTHONPATH$SARRA_LIB/../"
    else
        export PYTHONPATH="$PYTHONPATH:$SARRA_LIB/../"
    fi
fi
eval `application_dirs`
if [ ! -f "$CONFDIR"/admin.conf -o ! -f "$CONFDIR"/credentials.conf ]; then
 cat <<EOT
 ERROR:
 test users for each role: tsource, tsub, tfeed, bunnymaster (admin)
 need to be created before this script can be run.
 rabbitmq-server needs to be installed on a machine (FLOWBROKER) with admin account set and
 manually setup in "$CONFDIR"/admin.conf, something like this:

declare env FLOWBROKER=localhost
declare env SFTPUSER="`whoami`"
declare env TESTDOCROOT=${HOME}/sarra_devdocroot

broker amqp://tsource@localhost/
admin amqp://bunnymaster@localhost
feeder  amqp://tfeed@localhost
declare source tsource
declare subscriber tsub
declare subscriber anonymous

and "$CONFDIR"/credentials.conf will need to contain something like:

amqp://bunnymaster:PickAPassword@localhost
ftp://anonymous:anonymous@localhost:2121/
amqp://tsource:PickAPassword2@localhost
amqp://tfeed:PickAPassword3@localhost
amqp://tsub:PickAPassword4@localhost
amqp://anonymous:PickAPassword5@localhost
amqps://anonymous:anonymous@dd.weather.gc.ca
amqps://anonymous:anonymous@dd1.weather.gc.ca
amqps://anonymous:anonymous@dd2.weather.gc.ca

EOT
 exit 1
fi

# Shared variables by more than 1 flow test script
adminpw="`awk ' /bunnymaster:.*\@localhost/ { sub(/^.*:/,""); sub(/\@.*$/,""); print $1; exit }; ' "$CONFDIR"/credentials.conf`"
srposterlog="$LOGDIR/srposter_f00.log"
exnow=$LOGDIR/flow_setup.exchanges.txt
missedreport="$LOGDIR/missed_dispositions.report"
trivialhttplog="$LOGDIR/trivialhttpserver_f00.log"
trivialftplog="$LOGDIR/trivialftpserver_f00.log"
