#!/usr/bin/python3

# sundew_routing_2_sarra_subtopic.py 
# arguments pxtable1.conf ... pxtableN.conf 1day_brokerfilelist sender.conf
#
# This program reads all routing entries related to sender.conf
# Than it reads in

import os,re,sys

# config , path and client name

config=sys.argv[-1]
dirpat=os.path.dirname(config)
client=os.path.basename(config)
client=client.replace('.conf','')

# find routing table pattern match for that client

#print("client = %s" % client)

table_pattern_list=[]

print("Routing tables")

for table in sys.argv[1:-2]:
    print("\n%s products routed from %s\n" % (client,os.path.basename(table)))

    client_search_list=[]
    client_search_list.append(client)

    tablefile=open(table,'r')

    for line in tablefile:
        if line == None   : continue
        line = line.strip()
        if line == ''     : continue
        if line[0] == '#' : continue

        try :
                words=line.split()
                product_client_list=words[2].split(',')
        except:
                print("\nproblem with file: %s" % table, file=sys.stderr)
                print("line: %s" % line, file=sys.stderr)
                continue

        for fclient in client_search_list:
            if not fclient in product_client_list: continue
            if words[0] == 'clientAlias' :
               if words[1] in client_search_list : continue
               client_search_list.append(words[1])
               #print("alias = %s" % words[1])
            elif words[0] == 'key' :
               print("key %s" % words[1])
               pattern = '.*' + words[1].replace('_','.*') + '.*'
               table_entry = (pattern, re.compile(pattern) )
               table_pattern_list.append( table_entry )

    tablefile.close()

## load accept reject from client

config_pattern_list=[]

print("")
print("Sender config")
class Swallow_Config(object):
   def __init__(self):
       self.fname = None
       self.dname = None

   def perform(self,path):
       print("\n%s parsing of %s\n" % (client,os.path.basename(path)))
       configfile=open(path,'r')
       for line in configfile:
           if line == None   : continue
           line = line.strip()
           if line == ''     : continue
           if line[0] == '#' : continue
           words = line.split()
           try:
               if words[0] == 'include':
                  path2 = dirpat + '/' + words[1]
                  self.perform(path2)
                  continue
               elif words[0] == 'filename' :
                  self.fname = words[1]
               elif words[0] == 'directory' :
                  self.dname = words[1]
               elif words[0] in ['accept','reject']:
                  ar   = words[0] == 'accept'
                  ptrn = words[1]
                  if ptrn[0:1] != '.*' : ptrn = '.*' + ptrn
                  optn = None
                  if len(words) > 2 : optn = words[2]
                  entry = (ptrn,re.compile(ptrn),self.fname,self.dname,ar,optn)
                  config_pattern_list.append( entry )
           except:
                  print("\nproblem with file: %s" % path, file=sys.stderr)
                  print("line: %s" % line, file=sys.stderr)

       configfile.close()

directory=None
filename=None
swallow_config=Swallow_Config()
swallow_config.perform(config)

# check in one day of ddi products

resulting_dict={}

# get the number of lines of products to show progress

cmd='wc -l ' + sys.argv[-2]
import datetime,subprocess,time
answer=subprocess.check_output(cmd.split(' '))
parts = answer.split(b' ')
NL=int(parts[0].decode('utf-8'))

# ingest all products from a file in this routing mechanisms
# trying to find subtopics

i=0
now=time.time()
print("")
print("%s do product routing from file of %s" % (client,sys.argv[-2]), file=sys.stderr)
print("%s file proposed products %d" % (client,NL ), file=sys.stderr)
print("%s routing table entries  %d" % (client,len(table_pattern_list)), file=sys.stderr)
print("%s accept/reject entries  %d" % (client,len(config_pattern_list)), file=sys.stderr)

productfile=open(sys.argv[-2],'r')
for productline in productfile:
    i = i + 1

    # all of this is just to give an idea of the time
    # it will take to do the whole file

    percent= 100.0*i/NL
    span   = time.time()-now
    speed  = span/i
    left   = speed * (NL-i)
    lefthh = left/3600
    leftmm = (lefthh - int(lefthh)) * 60
    leftss = (leftmm - int(leftmm)) * 60

    print("\r %f%% (%d of %d) spent %f , left %.2d:%.2d:%.2d" % (percent,i,NL,span,int(lefthh),int(leftmm),int(leftss)), file=sys.stderr, end = '')

    # product extracted from line

    parts=productline.split()
    product=parts[-1]

    # check routingtable match

    matched =False
    for pattern,rpattern in table_pattern_list :

        # routing table not matching this product to this client...

        if not rpattern.match(product): continue

        # ok matched routing table ... see how it goes with sender config

        for entry in config_pattern_list:
            ptrn,cpattern,fname,dname,accept,optn = entry

            # product not configured in sender
            if not cpattern.match(product) : continue

            # ok this product matched and accept/reject pattern

            matched = True

            # HERE COMMENT IF YOU WANT rejects to be analysed too

            #if not accept : break

            # ok it matched an accept or reject

            dirname  = os.path.dirname(product)+ '/'
            dirname  = re.sub('/[0-9][0-9]/','/*/',dirname)
            parts    = dirname.split('/')
            dirname  = '*/'+ '/'.join(parts[1:])
            subtopic = dirname.replace('/','.')
            if subtopic[-1] == '.' :
               subtopic += '#'
               if dirname[-1] != '*' : dirname  += '*'
            else:
               subtopic += '.#'
               dirname  += '/*'
               if dirname[-1] != '*' : dirname  += '/*'
            dirname   = dirname.replace('*','.*')

            # preparing to add some results

            if not entry in resulting_dict :
               resulting_dict[entry] = {}

            rdict = resulting_dict[entry]

            if not subtopic in rdict :
               rdict[subtopic] = {}

            ardict = rdict[subtopic]

            if dirname[-2:] == '.*' : dirname = dirname[:-2]

            # product accepted
            if accept :
               arline = "accept  %s%s" % (dirname,ptrn)
               if optn: arline += ' ' + optn

            # product rejected
            else :
               arline   = "reject  %s%s" % (dirname,ptrn)

            # add if not already there
            if not arline in ardict :
               ardict[arline] = accept

            # we are done with this product
            break

        # product matched 
        if matched : break

#
productfile.close()

# convert configs

print("")
print("%s rewriting configs with infos discovered")
print("")
class Convert_Config(object):
   def __init__(self):
       self.ifname = None
       self.idname = None

   def perform(self,path):
       import shutil
       print("%s need the rewriting of %s" % (client,path))
       old = path + '.sundew'
       os.rename(path,old)
       oldconfigfile=open(old,'r')
       fp = configfile=open(path,'w')
    
       for line in oldconfigfile:
           if line == None   : continue
           tline = line.strip()
           if tline == ''     :
              fp.write(line)
              continue
           if line[0] == '#' :
              fp.write(line)
              continue
           words = line.split()
           try:
               if words[0] == 'include':
                  fp.write(line)
                  path2 = dirpat + '/' + words[1]
                  self.perform(path2)
                  continue
               elif words[0] == 'filename' :
                  fp.write(line)
                  self.ifname = words[1]
               elif words[0] == 'directory' :
                  fp.write(line)
                  self.idname = words[1]
               elif words[0] in ['accept','reject']:
                  ioptn   = None
                  if len(words) > 2 : ioptn = words[2]
                  iaccept = words[0] == 'accept'
                  matched = False
                  iptrn = words[1]
                  if iptrn[0:1] != '.*' : iptrn = '.*' + iptrn
                  for entry in resulting_dict:
                      ptrn,cpattern,fname,dname,accept,optn = entry
                      if dname  != self.idname  : continue
                      if fname  != self.ifname  : continue
                      if accept != iaccept : continue
                      if ptrn   != iptrn   : continue
                      if optn   != ioptn   : continue

                      matched = True
                      rdict=resulting_dict[entry]

                      for s in rdict :
                          fp.write("subtopic %s\n" % s)
                          ardict = rdict[s]
                          for l in ardict:
                              fp.write("%s\n" % l)

                  if not matched :
                     fp.write(line)

               else:
                  fp.write(line)
           except:
                  print("problem when converting: %s" % line,file=sys.stderr)

       oldconfigfile.close()
       fp.close()

convert_config=Convert_Config()
convert_config.perform(config)
