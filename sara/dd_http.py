#!/usr/bin/python3

import os, urllib.request, urllib.error, sys

def http_download(this, msg, iuser,ipassword, target_file,offset,length) :

    url       = msg.url
    urlstr    = url.geturl()
    user      = url.username
    password  = url.password

    if iuser     != None : user = iuser
    if ipassword != None : password = ipassword

    try :
            # create a password manager                
            if user != None :                          
                # Add the username and password.
                password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
                password_mgr.add_password(None, urlstr,user,passwd)
                handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
                        
                # create "opener" (OpenerDirector instance)
                opener = urllib.request.build_opener(handler)
    
                # use the opener to fetch a URL
                opener.open(urlstr)
    
                # Install the opener.
                # Now all calls to urllib2.urlopen use our opener.
                urllib.request.install_opener(opener)

            # byte range if needed
            req   = urllib.request.Request(urlstr)
            str_range = ''
            if msg.partflg == 'i' :
               str_range = 'bytes=%d-%d'%(msg.offset,msg.offset+msg.length-1)
               req.headers['Range'] = str_range
                   
            #download file

            if str_range != '' :
               this.logger.info('Inserting: %s %s %s %d %d' % (urlstr,str_range,target_file,offset,msg.length))  
            else :
               this.logger.info('Downloads: %s %s' % (urlstr,target_file))  

            response = urllib.request.urlopen(req)
            ok,code,message = write_to_file(this,response,target_file,offset,msg.length)                    

            return ok,code,message
                
    except urllib.error.HTTPError as e:
           return False,e.code,str(e.reason)
    except urllib.error.URLError as e:
           return False,e.code,str(e.reason)
    except:
           (stype, svalue, tb) = sys.exc_info()
           return False,499,str(svalue)


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
