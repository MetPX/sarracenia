#!/bin/bash

tstdir="`pwd`"
httpdocroot=`cat $tstdir/.httpdocroot`
cd

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

find "$httpdocroot"/cfr -type f -print | sed 's/\/cfr\//\/cfile\//' | xargs -n1 ls -al > /dev/null
find "$httpdocroot"/cfr -type l -print | sed 's/\/cfr\//\/cfile\//' | xargs -n1 ls -al > /dev/null
