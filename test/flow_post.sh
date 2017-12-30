#!/bin/bash

# script to be started by flow_setup.sh which runs sr_post in the background.

# The directory we run the flow test scripts in...
tstdir="`pwd`"

httpdocroot=`cat $tstdir/.httpdocroot`

# sr_post initial start
srpostdir=`cat $tstdir/.httpdocroot`/sent_by_tsource2send
srpostlstfile_new=$httpdocroot/srpostlstfile.new
srpostlstfile_old=$httpdocroot/srpostlstfile.old

echo > ${srpostlstfile_old}
# sr_post call

function do_sr_post {

   cd $srpostdir

   # sr_post testing START
   # TODO - consider if .httpdocroot ends with a '/' ?
   ls $srpostdir/* > $srpostlstfile_new
   # Obtain file listing delta
   srpostdelta=`comm -23 $srpostlstfile_new $srpostlstfile_old`

   if [ "$srpostdelta" == "" ]; then
      return
   fi

   sr_post -c test2_f61.conf -p $srpostdelta 

   cp -p $srpostlstfile_new $srpostlstfile_old

   do_sr_post

}

# sr_post initial end

while true; do
   sleep 10
   do_sr_post
done

