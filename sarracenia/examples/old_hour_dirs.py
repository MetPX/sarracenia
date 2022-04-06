#!/usr/bin/env python3
"""
  assume directories are named
  YYYYMMDDHHTHH
 
  after the UTC date when the first product within it is received.
   
  this script looks at the list of directories and removes the ones older
  than requested.  Sample invocation:
 
   python3 old_hour_dirs.py "5 hours ago" /Project/web_root
 
"""

import dateparser, os, random, shutil, sys, time

how_many_hours = sys.argv[1]

try:
    os.chdir(sys.argv[2])
except:
    print("Second argument should directory I can visit")
    exit(2)

cutoff = dateparser.parse(how_many_hours)

print("last is: %s\n" % cutoff)

old_dirs = []

for d in os.listdir('.'):
    ddt = dateparser.parse(d, ['%Y%m%dT%H'])
    print("this one is: %s\n" % ddt)
    if ddt is not None and ddt < cutoff:
        old_dirs.append(d)
        continue
    print("skipping: %s" % d)

old_dirs.sort()
random.shuffle(old_dirs)
for d in old_dirs:

    while True:
        try:
            print("shutil.rmtree(%s)\n" % d)
            shutil.rmtree(d)

            if not os.path.isdir(d):
                print('succeeded? %s failed isdir' % d)
                break
            print("ugh. rmtree(%s) succeeded, but it is still there" % (d))
            time.sleep(30)
        except Exception as ex:
            print("ugh. rmtree(%s) failed: %s" % (d, ex))
            time.sleep(30)
