#!/usr/bin/env python3

help_str =  \
"""
   sr_convert_log2save <logfile>

   sr_log2save reads the _log lines from the given file, assumed to be a log of a sarracenia component, where
   the _log lines are written by a plugin such as post_log, msg_log, or file_log.

   For each log line, it writes a corresponding line to standard output in the 'save' save format, readable
   by sr_shovel and sr_sender for -restore, and -restore2queue modes.

"""
import json
import sys
import urllib
import urllib.parse

if len(sys.argv) < 2 :
   print( help_str )


with open( sys.argv[1], "r" ) as log_file:
    for m in log_file:
        f = m.split()

        if f[3][-4:]  != '_log' :
           continue

        #print( "line:  %s" % m )
        timestamp=f[4].split('=')[1]
        
        theslash=10+f[5][10:].index('/')
        
        path=f[5][theslash+1:]
        newurl=f[5][0:theslash]
        notice="%s %s %s" % ( timestamp, newurl, path )

        jsonstr=' '.join(f[6:])[8:]
        topic='v02.post' + path.replace('/','.')

        print ( "[ \"%s\", %s, \"%s\" ] " % ( topic, jsonstr, notice ))
