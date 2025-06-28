import datetime
import os
import os.path
import re
import sarracenia.config
import sys

keep_count=5

print( 'EXPERIMENTAL log rotation tool to deal with a bug on windows' )
print( 'bug details: https://github.com/MetPX/sarracenia/issues/785' )
print( 'usage: accept an integer argument: number of old logs to keep, defaults to $keep_count' )
print( 'it does a log rotation each time it is called, if there is a current log to rotate')

if len(sys.argv) > 1:
    print(f" logs to keep: {sys.argv[1]}")
    keep_count=int(sys.argv[1])


timesuffix=str(datetime.datetime.now()).replace(' ','_').replace(':','_')[0:19]
logdir=sarracenia.config.user_cache_dir('sr3','MetPX') + os.sep + 'log'
print( f"log directory is: {logdir}")
current_log_pattern=re.compile(".*\.log$")
current_logs=[]
old_to_delete=[]
old_logs=[]
current_log_root=None
if not os.path.exists(logdir) or not os.path.isdir(logdir):
    print( "log dir does not exist")
    sys.exit(1)
existing_files=sorted(os.listdir(logdir))
os.chdir(logdir)
for l in existing_files:
    if current_log_pattern.match(l):
        old_name=l+'_'+timesuffix
        print( f"found {l} to be renamed to {old_name}")
        os.rename( l, old_name)
        current_log_root=l
        old_logs=[]
    elif current_log_root and l.startswith(current_log_root):
        old_logs.append(l)
    else:
        if len(old_logs) > 0:
            if len(old_logs) > keep_count:
                old_to_delete.extend(old_logs[0:-keep_count])
            old_logs=[]
        else:
            print( f"skipping {l}")

if len(old_to_delete) == 0:
    print( "no old logs to delete")
else:
    for old_log in old_to_delete:
        print( f"removing {old_log}")
        os.unlink(old_log)
