#!/bin/bash

export SR_POST_CONFIG=""
export LD_PRELOAD=""

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

echo "======================================================="
echo "list"
echo "======================================================="

# list
sr_cpost     list
sr_cpump     list
sr_poll      list
sr_post      list
sr_report    list
sr_sarra     list
sr_sender    list
sr_shovel    list
sr_subscribe list
sr_watch     list
sr_winnow    list


# edit, log omitted   list above, remove below

for action in add disable enable; do

echo "======================================================="
echo $action
echo "======================================================="


touch aaa.conf
sr_cpost    $action aaa.conf 2> /dev/null;
ls -al $CONFDIR/cpost/aaa.*;

touch aaa.conf
sr_cpump    $action aaa.conf 2> /dev/null;
ls -al $CONFDIR/cpump/aaa.*;

    for PGM in poll report sarra sender shovel subscribe watch winnow; do

        touch aaa.conf
        sr_$PGM    $action aaa.conf
        ls -al $CONFDIR/$PGM/aaa.*;
    done
done

echo "======================================================="
echo remove
echo "======================================================="


# remove
sr_cpost     remove aaa.conf
sr_cpump     remove aaa.conf
sr_poll      remove aaa.conf
#sr_post      remove aaa.conf
sr_report    remove aaa.conf
sr_sarra     remove aaa.conf
sr_sender    remove aaa.conf
sr_shovel    remove aaa.conf
sr_subscribe remove aaa.conf
sr_watch     remove aaa.conf
sr_winnow    remove aaa.conf



echo "======================================================="
echo status
echo "======================================================="


# status
#sr_cpost     status
#sr_cpump     status
sr_poll      status
#sr_post      status
sr_report    status
sr_sarra     status
sr_sender    status
sr_shovel    status
sr_subscribe status
sr_watch     status
sr_winnow    status
