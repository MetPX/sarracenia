#!/usr/bin/env python3

help_str =  \
"""
 
   FIXME: early days, do not know if this works yet!

   sr_convert_log2save <logfile>

   sr_log2save reads the _log lines from the given file, assumed to be a log of a sarracenia component, where
   the _log lines are written by a plugin such as post_log, msg_log, or file_log.

   For each log line, it writes a corresponding line to standard output in the 'save' save format, readable
   by sr_shovel and sr_sender for -restore, and -restore2queue modes.

"""
import sys

def main(): 
    if len(sys.argv) < 2 :
       log_file = sys.stdin
    else:
       log_file = open( sys.argv[1], "r" ) 
    
    for m in log_file:
            f = m.split()
    
            if f[3][-4:]  != '_log' :
               continue
    
            timestamp=f[4].split('=')[1]
            
            theslash=10+f[5][10:].index('/')
            path=f[5][theslash+1:]
            newurl=f[5][0:theslash]
    
            notice="%s %s %s" % ( timestamp, newurl, path )
    
            headers=' '.join(f[6:])[8:].replace("'","\"")
            topic='v02.post' + path.replace('/','.')
    
            print ( "[ \"%s\", %s, \"%s\" ] " % ( topic, headers, notice ))
    
    log_file.close()


if __name__=="__main__":
    main()
               
