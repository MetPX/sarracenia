#!/usr/bin/python3

import socket,sys,time
import paramiko
from   paramiko import *
import urllib.request, urllib.error

try :    from dd_util      import *
except : from sara.dd_util import *

class dd_download(object):

    def __init__(self,logger):

        self.logger  = logger

        self.lfile   = None
        self.str_url = None
        self.url     = URL()

        self.user        = None
        self.password    = None
        self.ssh_keyfile = None

        self.flags    = Flags()
        self.checksum = self.flags.checksum

        self.bufsize  = 128 * 1024 # read/write buffer size

        self.clustered        = False
        self.recompute_chksum = False


    def chunk_filename(self, chunksize, current_block ):
        parts = self.lfile.split(os.sep)
        fdir  = os.sep.join(parts[:-1])
        fname = parts[-1]
        chunk_fname = '.' + fname + '.%d.%d' % (chunksize, current_block )
        return fdir + os.sep + chunk_fname

    def chunk_insert(self, lfile, loffset, length, chunksize, current_block ):
        cfile = self.chunk_filename( chunksize, current_block )
        if not os.path.isfile(cfile) : return False

        str_range = 'bytes=%d-%d'%(loffset,loffset+length-1)
        self.logger.info('Inserting: %s %s %s' % (cfile,lfile,str_range))  

        fp = open(cfile,'rb')
        ok = self.write_to_file(fp,lfile,loffset,length)
        fp.close() 

        if ok : os.unlink(cfile)

        return ok

    def download(self,lfile,loffset,roffset,length,fsiz):
        downloaded = False
        if self.url.protocol == 'http' :
           downloaded = self.http_download(lfile,loffset,roffset,length,fsiz)
        if self.url.protocol == 'sftp' :
           downloaded = self.sftp_download(lfile,loffset,roffset,length,fsiz)
        return downloaded

    def http_download(self,lfile,loffset,roffset,length,fsiz):
        url    = self.url.get_nocredential()
        user   = self.url.user
        passwd = self.url.password

        if self.user     != None : user   = self.user
        if self.password != None : passwd = self.password

        try :
                # create a password manager                
                if user != None :                          
                    # Add the username and password.
                    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
                    password_mgr.add_password(None, url,user,passwd)
                    handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
                        
                    # create "opener" (OpenerDirector instance)
                    opener = urllib.request.build_opener(handler)
    
                    # use the opener to fetch a URL
                    opener.open(url)
    
                    # Install the opener.
                    # Now all calls to urllib2.urlopen use our opener.
                    urllib.request.install_opener(opener)

                # byte range if needed
                req   = urllib.request.Request(url)
                str_range = ''
                if length != 0 :
                   str_range = 'bytes=%d-%d'%(roffset,roffset+length-1)
                   req.headers['Range'] = str_range
                else :
                   length = fsiz
                   
                #download file

                if str_range != '' :
                   self.logger.info('Inserting: %s %s %s' % (url,lfile,str_range))  
                else :
                   self.logger.info('Downloads: %s %s' % (url,lfile))  

                response = urllib.request.urlopen(req)
                ok = self.write_to_file(response,lfile,loffset,length)                    

                return ok
                
        except urllib.error.HTTPError as e:
                self.logger.error('Download failed 1: %s', url)                    
                self.logger.error('Server couldn\'t fulfill the request. Error code: %s, %s', e.code, e.reason)
        except urllib.error.URLError as e:
                self.logger.error('Download failed 2: %s', url)                                    
                self.logger.error('Failed to reach server. Reason: %s', e.reason)            
        except:
                self.logger.error('Download failed 3: %s', url )
                (stype, svalue, tb) = sys.exc_info()
                self.logger.error("Type: %s, Value: %s,  ..." % (stype, svalue))
                self.logger.error('Uexpected error')              
        return False

    def get(self, chunksize, block_count, remainder, current_block, str_flags, data_sum, from_chunk = False ):

        self.start_timer()

        # ingest flags
        
        self.flags.from_str(str_flags)

        self.checksum = self.flags.checksum

        # setting notice

        self.dnotice.set_chunk(chunksize,block_count,remainder,current_block,str_flags,data_sum)

        # get chunk info

        r_offset,r_length,r_fsiz = Seekinfo(chunksize, block_count, remainder, current_block )

        r_lastchunk = (current_block == block_count-1)

        # check if chunk update needed

        l_needs_update,l_fsiz = self.update(self.lfile, r_offset,r_length,r_fsiz,str_flags,data_sum )

        # needs to be truncated maybe

        to_truncate = ( r_lastchunk and r_fsiz < l_fsiz )

        # update from chunk file

        if from_chunk :
           insert = self.chunk_insert(self.lfile, r_offset, r_length, chunksize, current_block )
           if to_truncate : self.truncate(self.lfile,l_fsiz,r_fsiz)
           if insert or to_truncate :
              if self.recompute_chksum : self.dnotice.data_sum = self.checksum(self.lfile,r_offset,r_length)
              self.publish()
           return insert
           
        # if not needed everything is ok

        if not l_needs_update :
           self.logger.info("Unchanged: %s " % self.lfile )
           if to_truncate : 
              self.truncate(self.lfile,l_fsiz,r_fsiz)
           self.publish(message=to_truncate)
           return True

        # should we put the chunk straight in the file

        infile   = False
        l_offset = r_offset
        if l_offset <= l_fsiz : infile = True

        # if we cannot download for now... keep chunk info
        if not infile and not self.flags.inplace :
           cfile   = self.chunk_filename( chunksize, current_block )
           loffset = 0
           ok      = self.download(cfile,loffset,roffset,r_length,r_fsiz)
           if ok and self.recompute_chksum :
              self.dnotice.data_sum = self.checksum(self.lfile,r_offset,r_length)
           return ok

        # special case download the entire file
        length = r_length
        if block_count == 1 : length = 0

        # go ahead and download in file
        downloaded = self.download(self.lfile,l_offset,r_offset,length,r_fsiz)

        if to_truncate: self.truncate(self.lfile,l_fsiz,r_fsiz)
        if downloaded :
           if self.recompute_chksum : self.dnotice.data_sum = self.checksum(self.lfile,l_offset,length)
           self.publish()

        if not downloaded   : return False
        #if self.clustered : return True
        
        # process with chunk file needed ?
        next_block = current_block + 1
        while next_block < block_count :
           cfile = self.chunk_filename( chunksize, next_block )
           if not os.path.isfile(cfile) : break
           self.logger.info("Detecting: %s " % cfile )
           downloaded = self.get( chunksize, block_count, remainder, next_block, str_flags, data_sum, True )
           if not downloaded : break 
           next_block = next_block + 1

        return True

    def get_elapse(self):
        return time.time()-self.tbegin

    def publish(self,code=202,message=True,log=True):

        str_key = self.dkey.get()
        body    = self.dnotice.get()

        if message and self.pub != None:
           filename = os.path.basename(self.lfile)
           self.pub.publish('xpublic',str_key,body,filename)
           self.logger.info("Publishes: %s   key      = %s" % ('xpublic',str_key))
           self.logger.info("Publishes: %s   body     = %s" % ('xpublic',body) )

        if log and self.log != None:
           log_key  = str_key.replace('.post.','.log.')
           body    += ' %d %s %s %f' % (code,socket.gethostname(),self.url.user,self.get_elapse())
           self.log.publish('log',log_key,body,'log')


    def set_key(self,dkey):
        self.dkey = dkey
        
    def set_local_file(self,lfile):
        self.lfile = lfile

    def set_notice(self,dnotice):
        self.dnotice = dnotice

    def set_clustered(self,clustered):
        self.clustered = clustered

    def set_publish(self,pub,log):
        self.pub = pub
        self.log = log

    def set_recompute(self,recompute):
        self.recompute_chksum = recompute

    def set_url(self,url):
        self.str_url = url
        self.url.set(url)

    def sftp_download(self,lfile,loffset,roffset,length,fsiz):
        host        = self.url.host
        port        = self.url.port
        user        = self.url.user
        passwd      = self.url.password

        ssh_keyfile = self.ssh_keyfile
        if self.user     != None : user   = self.user
        if self.password != None : passwd = self.password

        cdir     = self.url.path.replace(self.url.filename,'')
        cfile    = self.url.filename
        url      = self.url.get_nocredential()

        try :
                self.t = None
                if port == None : 
                   self.t = paramiko.Transport(host)
                else:
                   t_args = (host,port)
                   self.t = paramiko.Transport(t_args)

                if ssh_keyfile != None :
                   key=DSSKey.from_private_key_file(ssh_keyfile,password=None)
                   self.t.connect(username=user,pkey=key)
                else:
                   self.t.connect(username=user,password=passwd)

                self.sftp = paramiko.SFTP.from_transport(self.t)
                self.sftp.chdir(cdir)

                #download file
                str_range = ''
                if length == 0 :
                   self.logger.info('Downloads:  %s %s' % (url,lfile))  
                   self.sftp.get(cfile,lfile)
                   ok = True
                else :
                   str_range = 'bytes=%d-%d'%(roffset,roffset+length-1)
                   response  = self.sftp.file(cfile,'rb',self.bufsize)
                   if roffset != 0 : response.seek(roffset,0)
                   self.logger.info('Inserting: %s %s %s' % (url,lfile,str_range))  
                   ok = self.write_to_file(response,lfile,loffset,length)                    

                try    : self.sftp.close()
                except : pass
                try    : self.t.close()
                except : pass

                return ok
                
        except:
                (stype, value, tb) = sys.exc_info()
                self.logger.error("Download failed %s. Type: %s, Value: %s" % (self.url.get_nocredential(), stype ,value))

        return False

    def start_timer(self):
        self.tbegin = time.time()
  
    def truncate(self,lfile,l_fsiz,r_fsiz):
        fp = open(lfile,'r+b')
        fp.truncate(r_fsiz)
        fp.close()
        self.logger.info("Truncated: %s (%d to %d)" % (lfile,l_fsiz,r_fsiz) )

    def update(self, lfile, offset, length, fsiz, str_flags, data_sum ):
        lfsiz  = 0

        if not os.path.isfile(lfile) : return True,lfsiz

        lstat  = os.stat(lfile)
        lfsiz  = lstat[stat.ST_SIZE]

        echunk = offset + length - 1
        if echunk >= lfsiz : return True,lfsiz

        ldata_sum = self.checksum(lfile,offset,length)
        if ldata_sum != data_sum : return True,lfsiz
   
        return False,lfsiz
                
    def write_to_file(self,req,lfile,loffset,length) :
        # file should exists
        if not os.path.isfile(lfile) :
           fp = open(lfile,'w')
           fp.close()

        # file open read/modify binary
        fp = open(lfile,'r+b')
        if loffset != 0 : fp.seek(loffset,0)

        nc = int(length/self.bufsize)
        r  = length % self.bufsize

        # loop on bufsize if needed
        i  = 0
        while i < nc :
              chunk = req.read(self.bufsize)
              if len(chunk) != self.bufsize :
                 self.logger.debug('length %d and bufsize = %d' % (len(chunk),self.bufsize))
                 self.logger.error('source data differ from notification... abort')
                 if i > 0 : self.logger.error('product corrupted')
                 return False
              fp.write(chunk)
              i = i + 1

        # remaining
        if r > 0 :
           chunk = req.read(r)
           if len(chunk) != r :
              self.logger.debug('length %d and remainder = %d' % (len(chunk),r))
              self.logger.error('source data differ from notification... abort')
              return False
           fp.write(chunk)

        fp.close()

        return True
