#!/usr/bin/python3

"""
  Msg_Cclean_F91
  
  plugin that receives a message from shovel cclean_f90 ... for each product... python side
  - it checks if the propagation was ok.
  - it removes the product instances at the watch level
  - it posts the product again (shovel clean_f92 )

  when a product is not fully propagated, it is put in the retry list

  The post_log count should be the same as the original flow test count

"""
import os,stat,time

class Msg_Cclean_F91(object): 

    def __init__(self,parent):
        pass

    def log_state(self,parent,propagated,ext=None):
        logger = parent.logger

        if not ext :
           if not os.path.isfile(self.cpost_f30_path) : logger.warning("%s not found" % self.cpost_f30_path)
           if not os.path.isfile(self.csubs_f40_path) : logger.warning("%s not found" % self.csubs_f40_path) 
        else:
           if not os.path.isfile(self.cpost_f30_path+ext) : logger.warning("%s not found" % self.cpost_f30_path+ext)
           if not os.path.isfile(self.csubs_f40_path+ext) : logger.warning("%s not found" % self.csubs_f40_path+ext) 
        logger.warning("propagated = %d" % propagated) 

    def on_message(self,parent):
        import shutil

        logger = parent.logger
        msg    = parent.msg
        root   = parent.currentDir
        relp   = msg.relpath

        logger.info("msg_cclean_f91.py on_message")

        if 'cclean_f90' in msg.headers :
           ext = msg.headers['cclean_f90']
           msg.headers['cclean_f91'] = ext

        else:
           logger.info("msg_log received: %s %s%s topic=%s lag=%g %s" % \
           tuple( msg.notice.split()[0:3] + [ msg.topic, msg.get_elapse(), msg.hdrstr ] ) )
           logger.error("The message received is incorrect not from shovel cclean_f90")
           return False


        # build all 3 paths of a successfull propagated path

        if relp[0] != '/' : relp = '/' + relp

        self.cpost_f30_path = root + '/cfr'      + relp   # sarra
        self.csubs_f40_path = root + '/cfile'    + relp   # subscribe t_sub

        # propagated count 

        propagated = 0
        if os.path.isfile(self.cpost_f30_path+ext) : propagated += 1
        if os.path.isfile(self.csubs_f40_path+ext) : propagated += 1

        # propagation unfinished ... (or test error ?)
        # retry message screened out of on_message is taken out of retry
        # here we enforce keeping it... to verify propagation again

        if propagated != 2 :
           logger.warning("%s not fully propagated" % relp )
           # if testing
           self.log_state(parent,propagated,ext)
           parent.consumer.msg_to_retry()
           return False

        # ok it is everywhere ...  # do big cleanup
        # should propagate to sr_subscribe c f40

        try   : os.unlink( self.cpost_f30_path)
        except: logger.warning("%s already deleted ?" % self.cpost_f30_path)

        try   : os.unlink( self.cpost_f30_path+ext)
        except: logger.warning("%s already deleted ?" % self.cpost_f30_path+ext)

        del msg.headers['cclean_f90']

        return True

self.plugin='Msg_Cclean_F91'
