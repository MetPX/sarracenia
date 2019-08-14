#!/bin/bash

. ./flow_utils.sh

if [ ! "$1" ]; then
  printf "\n\nflow_trace.sh <filename>\n"
  printf "\n\ttrace the progress of a file through the flow test components in order\n\n"
  exit 1
fi

printf "FLOW f0x messages from data mart\n\n"
grep $1  $LOGDIR/sr_shovel_t_dd1_f00_01.log
grep $1  $LOGDIR/sr_shovel_t_dd2_f00_01.log

printf "\n\nFLOW f1x winnowing\n\n"
grep $1  $LOGDIR/sr_winnow*

printf "\n\nFLOW f2x download to local mirror\n\n"
grep $1  $LOGDIR/sr_sarra_* 

printf "\n\nFLOW f3x downloading from http://localhost to downloaded_by_sub_t f3x\n\n"
grep $1  $LOGDIR/sr_subscribe_t_f30_*.log


printf "\n\nFLOW f4x watch\n\n"
grep $1  $LOGDIR/sr_watch_f40_01.log

printf "\n\nFLOW f60 subscribe & sftp://localhost download to downloaded_by_sub_u\n\n"
grep $1  $LOGDIR/sr_subscribe_u_sftp_f60_01.log
grep $1  $LOGDIR/sr_subscribe_u_sftp_f60_0?.log

printf "\n\nFLOW f61 post\n\n"
grep $1 $srposterlog

printf "\n\nFLOW f62 poll \n\n"
grep $1 $LOGDIR/sr_poll_f62_01.log

#printf "\n\nFLOW f71 subscribe r to post \n\n"

printf "\n\nFLOW f71 subscribe q to poll \n\n"
grep $1  $LOGDIR/sr_subscribe_q_f71_*.log
