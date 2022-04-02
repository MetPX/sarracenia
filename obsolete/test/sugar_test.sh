#!/bin/bash

export SR_POST_CONFIG=""
export LD_PRELOAD=""

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

echo "======================================================="
echo "list"
echo "======================================================="

# list
if [ ! "$SARRA_LIB" ]; then
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
else
	"$SARRA_LIB"/sr_cpost.py     list
	"$SARRA_LIB"/sr_cpump.py     list
	"$SARRA_LIB"/sr_poll.py      list
	"$SARRA_LIB"/sr_post.py      list
	"$SARRA_LIB"/sr_report.py    list
	"$SARRA_LIB"/sr_sarra.py     list
	"$SARRA_LIB"/sr_sender.py    list
	"$SARRA_LIB"/sr_shovel.py    list
	"$SARRA_LIB"/sr_subscribe.py list
	"$SARRA_LIB"/sr_watch.py     list
	"$SARRA_LIB"/sr_winnow.py    list
fi
# edit, log omitted   list above, remove below

for action in add disable enable; do

echo "======================================================="
echo $action
echo "======================================================="


touch aaa.conf
if [ ! "$SARRAC_LIB" ]; then
	sr_cpost    				$action aaa.conf 2> /dev/null;
else
	"$SARRAC_LIB"/sr_cpost       $action aaa.conf 2> /dev/null;
fi
ls -al $CONFDIR/cpost/aaa.*;

touch aaa.conf
if [ ! "$SARRAC_LIB" ]; then
	sr_cpump    				$action aaa.conf 2> /dev/null;
else
	"$SARRAC_LIB"/sr_cpump      $action aaa.conf 2> /dev/null;
fi
ls -al $CONFDIR/cpump/aaa.*;

    for PGM in poll post report sarra sender shovel subscribe watch winnow; do

        touch aaa.conf
        if [ ! "$SARRA_LIB" ]; then
        	sr_$PGM    $action aaa.conf
        else 
        	"$SARRA_LIB"/sr_$PGM.py    $action aaa.conf
        fi

        ls -al $CONFDIR/$PGM/aaa.*;
    done
done

echo "======================================================="
echo remove
echo "======================================================="


# remove
if [ ! "$SARRAC_LIB" ]; then 
	sr_cpost     remove aaa.conf
	sr_cpump     remove aaa.conf
else 
	"$SARRAC_LIB"/sr_cpost     remove aaa.conf
	"$SARRAC_LIB"/sr_cpump     remove aaa.conf
fi

if [ ! "$SARRA_LIB" ]; then 
	sr_poll      remove aaa.conf
	sr_post      remove aaa.conf
	sr_report    remove aaa.conf
	sr_sarra     remove aaa.conf
	sr_sender    remove aaa.conf
	sr_shovel    remove aaa.conf
	sr_subscribe remove aaa.conf
	sr_watch     remove aaa.conf
	sr_winnow    remove aaa.conf
else 
	"$SARRA_LIB"/sr_poll.py      remove aaa.conf
	"$SARRA_LIB"/sr_post.py      remove aaa.conf
	"$SARRA_LIB"/sr_report.py    remove aaa.conf
	"$SARRA_LIB"/sr_sarra.py     remove aaa.conf
	"$SARRA_LIB"/sr_sender.py    remove aaa.conf
	"$SARRA_LIB"/sr_shovel.py    remove aaa.conf
	"$SARRA_LIB"/sr_subscribe.py remove aaa.conf
	"$SARRA_LIB"/sr_watch.py     remove aaa.conf
	"$SARRA_LIB"/sr_winnow.py    remove aaa.conf
fi



echo "======================================================="
echo status
echo "======================================================="


# status
if [ ! "$SARRA_LIB" ]; then 
	#sr_cpost     status
	#sr_cpump     status
	sr_poll       status
	#sr_post      status
	sr_report     status
	sr_sarra      status
	sr_sender     status
	sr_shovel     status
	sr_subscribe  status
	sr_watch      status
	sr_winnow     status
else
	#"$SARRA_LIB"/sr_cpost.py     status
	#"$SARRA_LIB"/sr_cpump.py     status
	"$SARRA_LIB"/sr_poll.py       status
	#"$SARRA_LIB"/sr_post.py      status
	"$SARRA_LIB"/sr_report.py     status
	"$SARRA_LIB"/sr_sarra.py      status
	"$SARRA_LIB"/sr_sender.py     status
	"$SARRA_LIB"/sr_shovel.py     status
	"$SARRA_LIB"/sr_subscribe.py  status
	"$SARRA_LIB"/sr_watch.py      status
	"$SARRA_LIB"/sr_winnow.py     status
fi
