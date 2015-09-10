#!/usr/bin/python3

import paramiko, sys
from   paramiko import *

def sftp_download(this, msg, iuser, ipassword, ssh_keyfile, target_file, offset, length ):
    url       = msg.url
    host      = url.hostname
    port      = url.port
    user      = url.username
    password  = url.password
    urlstr    = url.geturl()

    bufsize   = 10 * 1024 * 1024

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

            #download file
            str_range = ''
            if length == 0 :
               this.logger.info('Downloads:  %s %s' % (urlstr,target_file))  
               sftp.get(cfile,target_file)
               ok      = True
               code    = 201
               message = 'Created (Downloaded)'
            else :
               str_range = 'bytes=%d-%d'%(msg.offset,msg.offset+msg.length-1)
               response  = sftp.file(cfile,'rb',bufsize)
               if msg.offset != 0 : response.seek(msg.offset,0)
               this.logger.info('Inserting: %s %s %s' % (urlstr,target_file,str_range))  
               ok,code,message = write_to_file(response,target_file,offset,length)                    

            try    : sftp.close()
            except : pass
            try    : t.close()
            except : pass

            return ok,code,message
            
    except:
            (stype, svalue, tb) = sys.exc_info()
            this.logger.error("Download failed %s. Type: %s, Value: %s" % (urlstr, stype ,svalue))
            return False,499,str(svalue)

    return False,499,''

def write_to_file(this,req,lfile,loffset,length) :
    bufsize = 10 * 1024 * 1024
    # file should exists
    if not os.path.isfile(lfile) :
       fp = open(lfile,'w')
       fp.close()

    # file open read/modify binary
    fp = open(lfile,'r+b')
    if loffset != 0 : fp.seek(loffset,0)

    nc = int(length/bufsize)
    r  = length % bufsize

    # loop on bufsize if needed
    i  = 0
    while i < nc :
          chunk = req.read(bufsize)
          if len(chunk) != bufsize :
             this.logger.debug('length %d and bufsize = %d' % (len(chunk),bufsize))
             this.logger.error('source data differ from notification... abort')
             if i > 0 : this.logger.error('product corrupted')
             return False,417,'Expectation Failed'
          fp.write(chunk)
          i = i + 1

    # remaining
    if r > 0 :
       chunk = req.read(r)
       if len(chunk) != r :
          this.logger.debug('length %d and remainder = %d' % (len(chunk),r))
          this.logger.error('source data differ from notification... abort')
          return False,417,'Expectation Failed'
       fp.write(chunk)

    fp.close()

    return True,201,'Created (Downloaded)'

