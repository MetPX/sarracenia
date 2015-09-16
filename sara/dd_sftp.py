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
               ok = sftp_write_length(response,msg)
            else :
               ok = sftp_write(response,msg)

            try    : sftp.close()
            except : pass
            try    : t.close()
            except : pass

            return ok
            
    except:
            try    : sftp.close()
            except : pass
            try    : t.close()
            except : pass

            (stype, svalue, tb) = sys.exc_info()
            msg.logger.error("Download failed %s. Type: %s, Value: %s" % (urlstr, stype ,svalue))
            msg.code    = 499
            msg.message = 'sftp download problem'
            msg.log_error()

            return False

    msg.code    = 499
    msg.message = 'sftp download problem'
    msg.log_error()

    return False

# read all file no worry

def sftp_write(req,msg):
    if not os.path.isfile(msg.local_file) :
       fp = open(msg.local_file,'w')
       fp.close

    fp = open(msg.local_file,'r+b')
    if msg.local_offset != 0 : fp.seek(msg.local_offset,0)

    while True:
          chunk = req.read(msg.bufsize)
          if not chunk : break
          fp.write(chunk)

    fp.close()

    msg.code    = 201
    msg.message = 'Downloaded'
    msg.log_info()

    return True


# read exact length

def sftp_write_length(req,msg):
    # file should exists
    if not os.path.isfile(msg.local_file) :
       fp = open(msg.local_file,'w')
       fp.close()

    # file open read/modify binary
    fp = open(msg.local_file,'r+b')
    if msg.local_offset != 0 : fp.seek(msg.local_offset,0)

    nc = int(msg.length/msg.bufsize)
    r  =     msg.length%msg.bufsize

    # read/write bufsize "nc" times
    i  = 0
    while i < nc :
          chunk = req.read(msg.bufsize)
          fp.write(chunk)
          i = i + 1

    # remaining
    if r > 0 :
       chunk = req.read(r)
       fp.write(chunk)

    fp.close()

    msg.code    = 201
    msg.message = 'Downloaded'
    msg.log_info()

    return True

