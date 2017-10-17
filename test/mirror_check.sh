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

# sr_post initial start
tstdir="`pwd`"
httpdocroot=`cat $tstdir/.httpdocroot`

# MIRROR TEST

sr_cpost stop veille_f34 > /dev/null 2>&1
rm "$LOGDIR"/sr_cpost_veille_f34*.log 2> /dev/null

sr_subscribe stop cfile_f44 > /dev/null 2>&1
rm "$LOGDIR"/sr_subscribe_cfile_f44*.log 2> /dev/null

sr_cpost start veille_f34 > /dev/null 2>&1
sr_subscribe start cfile_f44 > /dev/null 2>&1

# preventive cleanup (previous runs)

cd "$httpdocroot"

cd cfr
rm *.copy* *.softlink *.link *.move 2> /dev/null
cd ..

cd cfile
rm *.copy* *.softlink *.link *.move 2> /dev/null
cd ..

# copy, link, softlink

cd cfr
ORIGINAL=`ls`
for f in $ORIGINAL; do
    cp "$f" "$f".copy
    cp "$f" "$f".copy2
    ln -s "$f" "$f".softlink
    ln "$f" "$f".link
done
COUNT=`ls| wc -l`

# expect the same in subscribe

cd ../cfile
TARGET_COUNT=`ls| wc -l`
while [ "${TARGET_COUNT}" != "${COUNT}" ]; do
      sleep 5
      TARGET_COUNT=`ls| wc -l`
      echo "(${TARGET_COUNT} of ${COUNT}) (COPY,SOFTLINK,LINK)"
done
echo "SUCCESS (COPY, SOFTLINK, LINK)"


# move files to a new file

cd ../cfr
for f in $ORIGINAL; do
    mv "$f".copy2 "$f".move
done
COUNT=`ls *.move| wc -l`
sleep 2

# expect the same in subscribe

cd ../cfile
TARGET_COUNT=`ls *.move| wc -l`
while [ "${TARGET_COUNT}" != "${COUNT}" ]; do
      sleep 5
      TARGET_COUNT=`ls *.move| wc -l`
      echo "(${TARGET_COUNT} of ${COUNT}) (MOVE)"
done
echo "SUCCESS (MOVE)"
echo


# remove copy, link, softlink

cd ../cfr
rm *.copy*
rm *.softlink
rm *.link
rm *.move
COUNT=`ls| wc -l`

# expect the same in subscribe

cd ../cfile
TARGET_COUNT=`ls| wc -l`
while [ "${TARGET_COUNT}" != "${COUNT}" ]; do
      sleep 5
      TARGET_COUNT=`ls| wc -l`
      echo "(${TARGET_COUNT} of ${COUNT}) (REMOVE)"
done
echo "SUCCESS (REMOVE)"

