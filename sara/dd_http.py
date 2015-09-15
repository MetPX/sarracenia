#!/usr/bin/python3

import os, urllib.request, urllib.error, sys

def http_download( msg, iuser, ipassword ) :

    url       = msg.url
    urlstr    = url.geturl()
    user      = url.username
    password  = url.password

    if iuser     != None : user     = iuser
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

            # set a byte range to pull from remote file
            req   = urllib.request.Request(urlstr)
            str_range = ''
            if msg.partflg == 'i' :
               str_range = 'bytes=%d-%d'%(msg.offset,msg.offset+msg.length-1)
               req.headers['Range'] = str_range
                   
            #download file

            msg.logger.info('Downloads: %s %s into %s %d-%d' % (urlstr,str_range,msg.local_file,msg.local_offset,msg.length))  

            response = urllib.request.urlopen(req)
            ok,code,message = http_write(response,msg)

            return ok,code,message
                
    except urllib.error.HTTPError as e:
           return False,e.code,str(e.reason)
    except urllib.error.URLError as e:
           return False,e.code,str(e.reason)
    except:
           (stype, svalue, tb) = sys.exc_info()
           return False,499,str(svalue)

def http_write(req,msg) :
    if not os.path.isfile(msg.local_file) :
       fp = open(msg.local_file,'w')
       fp.close

    fp = open(msg.local_file,'r+b')
    if msg.local_offset != 0 : fp.seek(msg.local_offset,0)

    # should not worry about length...
    # http provides exact data

    while True:
          chunk = req.read(msg.bufsize)
          if not chunk : break
          fp.write(chunk)

    fp.close()

    return True,201,'Created (Downloaded)'
