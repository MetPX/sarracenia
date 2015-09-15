#!/usr/bin/python3

import paramiko, os,sys
from   paramiko import *

def sftp_download( msg, iuser, ipassword, ssh_keyfile ):
    url       = msg.url
    host      = url.hostname
    port      = url.port
    user      = url.username
    password  = url.password
    urlstr    = url.geturl()

    if iuser     != None : user = iuser
    if ipassword != None : password = ipassword

    token    = url.path.split('/')
    
    cdir     = '/'.join(token[:-1])
    cfile    = token[-1]

    try :
            t = None
            if port == None : 
               t = paramiko.Transport(host)
            else:
               t_args = (host,port)
               t = paramiko.Transport(t_args)

            if ssh_keyfile != None :
               key=DSSKey.from_private_key_file(ssh_keyfile,password=None)
               t.connect(username=user,pkey=key)
            else:
               t.connect(username=user,password=password)

            sftp = paramiko.SFTP.from_transport(t)
            sftp.chdir(cdir)

            str_range = ''
            if msg.partflg == 'i' :
               str_range = 'bytes=%d-%d'%(msg.offset,msg.offset+msg.length-1)

            #download file

            msg.logger.info('Downloads: %s %s into %s %d-%d' % 
                (urlstr,str_range,msg.local_file,msg.local_offset,msg.local_offset+msg.length-1))


            response  = sftp.file(cfile,'rb',msg.bufsize)
            if msg.partflg == 'i' :
               response.seek(msg.offset,0)
               ok,code,message = sftp_write_length(response,msg)
            else :
               ok,code,message = sftp_write(response,msg)

            try    : sftp.close()
            except : pass
            try    : t.close()
            except : pass

            return ok,code,message
            
    except:
            (stype, svalue, tb) = sys.exc_info()
            msg.logger.error("Download failed %s. Type: %s, Value: %s" % (urlstr, stype ,svalue))
            return False,499,str(svalue)

    return False,499,''

def sftp_write(req,msg):
    if not os.path.isfile(msg.local_file) :
       fp = open(msg.local_file,'w')
       fp.close

    fp = open(msg.local_file,'r+b')
    if msg.local_offset != 0 : fp.seek(msg.local_offset,0)

    # read all file no worry

    while True:
          chunk = req.read(msg.bufsize)
          if not chunk : break
          fp.write(chunk)

    fp.close()

    return True,201,'Created (Downloaded)'


def sftp_write_length(req,msg):
    # file should exists
    if not os.path.isfile(msg.local_file) :
       fp = open(msg.local_file,'w')
       fp.close()

    # file open read/modify binary
    fp = open(msg.local_file,'r+b')
    if msg.local_offset != 0 : fp.seek(msg.local_offset,0)

    nc = int(msg.length/msg.bufsize)
    r  = msg.length % msg.bufsize

    # loop on bufsize if needed
    i  = 0
    while i < nc :
          chunk = req.read(msg.bufsize)
          if len(chunk) != msg.bufsize :
             msg.logger.debug('length %d and bufsize = %d' % (len(chunk),msg.bufsize))
             msg.logger.error('source data differ from notification... abort')
             if i > 0 : msg.logger.error('product corrupted')
             return False,417,'Expectation Failed'
          fp.write(chunk)
          i = i + 1

    # remaining
    if r > 0 :
       chunk = req.read(r)
       if len(chunk) != r :
          msg.logger.debug('length %d and remainder = %d' % (len(chunk),r))
          msg.logger.error('source data differ from notification... abort')
          return False,417,'Expectation Failed'
       fp.write(chunk)

    fp.close()

    return True,201,'Created (Downloaded)'

