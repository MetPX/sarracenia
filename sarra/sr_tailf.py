#/usr/bin/env python3
"""

replacement for tail -f to use on Windows systems that don't have it.

started with: https://gist.github.com/amitsaha/5990310

"""

#!/usr/bin/python3

import os,sys,time

def tail_file(filename, nlines):
    with open(filename) as qfile:
        qfile.seek(0, os.SEEK_END)
        endf = position = qfile.tell()
        linecnt = 0
        while position >= 0:
            qfile.seek(position)
            next_char = qfile.read(1)
            if next_char == "\n" and position != endf-1:
                linecnt += 1

            if linecnt == nlines:
                break
            position -= 1

        if position < 0:
            qfile.seek(0)

        print(qfile.read(),end='')

        while True:
           l=qfile.readline() 
           if (l):
              sys.stdout.write(l)
           else:
              time.sleep(0.2)

def main():
    filename = sys.argv[1]
    #nlines = int(sys.argv[2])
    tail_file(filename, 10)

if __name__ == '__main__':
    main()
