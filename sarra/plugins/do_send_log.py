#!/usr/bin/python3

"""
do_send_log : an example do_send that only logs for testing purpose
"""

class Do_Send_Log(object): 

   def __init__(self,parent):
       self.registered_list = [ 'ftp','ftps','sftp' ]
       self.proto = None
       self.batch = 0

   def registered_as(self) :
       return self.registered_list

   def do_send(self,parent):
       logger     = parent.logger
       msg        = parent.msg

       local_file = msg.relpath
       new_dir    = msg.new_dir
       new_file   = msg.new_file

       try :
              logger.info("transport send")
    
              if self.proto == None :
                 logger.info("transport send connects")
                 proto = True
        
              logger.info("cd %s (perm 775)" % new_dir )

              if msg.sumflg == 'R' :
                 logger.info("rm %s" % new_file )
                 return True

              if msg.sumflg == 'L' :
                 logger.info("symlink %s %s" % ( new_file, msg.headers['link'] ))
                 return True

              offset = 0
              if  msg.partflg == 'i': offset = msg.offset
    
              str_range = ''
              if msg.partflg == 'i' :
                 str_range = 'bytes=%d-%d'%(offset,offset+msg.length-1)
    
              #upload file
    
              if parent.inflight == None or msg.partflg == 'i' :
                 logger.info("put %s %s (%d,%d,%d)" % ( local_file, new_file, offset, offset, msg.length) )
              elif parent.inflight == '.' :
                 new_lock = '.'  + new_file
                 logger.info("put %s %s" % (local_file, new_lock ))
                 logger.info("rename %s %s" % (new_lock, new_file))
              elif parent.inflight[0] == '.' :

                 new_lock = new_file + parent.inflight
                 logger.info("put %s %s" % (local_file, new_lock ))
                 logger.info("rename %s %s" % (new_lock, new_file))
              elif parent.inflight == 'umask' :
                 logger.info("umask")
                 logger.info("put %s %s" % (local_file, new_file ))

              msg.logger.info('Sent: %s %s into %s/%s %d-%d' % 
                  (parent.local_file,str_range,new_dir,new_file,offset,offset+msg.length-1))

       except:
              logger.error("Couldn't send log")
              logger.debug('Exception details: ', exc_info=True)

       return True
               
self.plugin='Do_Send_Log'

