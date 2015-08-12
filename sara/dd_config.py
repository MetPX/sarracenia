#!/usr/bin/python3

import re,sys

try :    from dd_util      import *
except : from sara.dd_util import *

class dd_config:

    def __init__(self,logger,config=None,args=None):
        self.logger = logger

    def args(self,args):
        if args == None : return

        i = 0
        while i < len(args):
              n = self.option(args[i:])
              if n == 0 : n = 1
              i = i + n

    def config(self,path):
        if path == None : return
        try:
            f = open(path, 'r')
        except:
            (type, value, tb) = sys.exc_info()
            self.logger.error("Type: %s, Value: %s" % (type, value))
            return 

        for line in f.readlines():
            words = line.split()
            if (len(words) >= 2 and not re.compile('^[ \t]*#').search(line)):
                self.option(words)

        f.close()
    

    def isTrue(self,s):
        if  s == 'True' or s == 'true' or s == 'yes' or s == 'on' or \
            s == 'Yes'  or s == 'YES' or s == 'TRUE' or s == 'ON' or \
            s == '1'    or s == 'On' :
            return True
        else:
            return False


    def option(self,words):

        n = 0
        try:
                if   words[0] in ['include','-c']:
                     self.config(words[1])
                     n = 2
                elif words[0] in ['blocksize','-bz','--blocksize']:
                     self.blocksize = chunksize_from_str(words[1])
                     n = 2
                elif words[0] in ['basedir','-bd','--basedir']:
                     self.basedir = words[1]
                     n = 2
                elif words[0] in ['clustered','-cl','--clustered']:
                     if words[0][0:1] == '-' : 
                        self.clustered = True
                        n = 1
                     else :
                        self.clustered = self.isTrue(words[1])
                        n = 2
                elif words[0] in ['destination','-d','--destination'] :
                     self.destination.set(words[1])
                     n = 2
                elif words[0] in ['dest_exchange','-de','--destination_exchange']:
                     self.dest_exchange = words[1]
                     n = 2
                elif words[0] in ['dest_path','-dp','--destination_path']:
                     self.dest_path = words[1]
                     n = 2
                elif words[0] in ['exchange_key','-ek','--exchange_key']:
                     self.exchange_key.append(words[1])
                     n = 2
                elif words[0] in ['flags','-f','--flags']:
                     self.str_flags = words[1] 
                     self.flags.from_str(self.str_flags)
                     n = 2
                elif words[0] in ['instances','-i','--instances']:
                     self.instances = int(words[1])
                     n = 2
                elif words[0] in ['post','-p','--post'] :
                     self.post.set(words[1])
                     n = 2
                elif words[0] in ['randomize','-r','--randomize']:
                     if words[0][0:1] == '-' : 
                        self.randomize = True
                        n = 1
                     else :
                        self.randomize = self.isTrue(words[1])
                        n = 2
                elif words[0] in ['recompute_chksum','-rc','--recompute_chksum']:
                     if words[0][0:1] == '-' : 
                        self.recompute_chksum = True
                        n = 1
                     else :
                        self.recompute_chksum = self.isTrue(words[1])
                        n = 2
                elif words[0] in ['reconnect','-rr','--reconnect']:
                     if words[0][0:1] == '-' : 
                        self.reconnect = True
                        n = 1
                     else :
                        self.reconnect = self.isTrue(words[1])
                        n = 2
                elif words[0] in ['source','-s','--source_url']:
                     self.source.set(words[1])
                     n = 2
                elif words[0] in ['src_exchange','-se','--source_exchange']:
                     self.src_exchange = words[1]
                     n = 2
                elif words[0] in ['ssh_keyfile','-sk','--ssh_keyfile']:
                     self.ssh_keyfile = words[1]
                     n = 2
                elif words[0] in ['strip','-st','--strip']:
                     self.strip = int(words[1])
                     n = 2
                elif words[0] in ['tag','-t','--tag']:
                     self.tag = words[1] 
                     n = 2
                elif words[0] in ['transmission','-tr','--transmission_url']:
                     self.transmission.set(words[1])
                     n = 2
                elif words[0] in ['trx_basedir','-tbd','--transmission_basedir']:
                     self.trx_basedir = words[1]
                     n = 2
                elif words[0] in ['watch_dir','-wd','--watch_directory']:
                     self.watch_dir = words[1]
                     n = 2
        except:
                pass

        return n
