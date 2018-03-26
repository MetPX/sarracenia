#!/usr/bin/python3

"""
  Msg_Cclean_F90
  
  plugin that is used in shovel cclean_f90 ... for each product... C side
  - it checks if the propagation was ok.
  - it randomly set a test in the veille_f34.conf for propagation
  - it remove the original product ... which is propagated too
  - it posts the product again (more test in shovel cclean_f91)

  when a product is not fully propagated, it is put in the retry list

  The post_log count should be the same as the original flow test count

  The posted message contains a tag in the header for the test performed
  which is the extension used for the test

"""
import os,stat,time

class Msg_Cclean_F90(object): 

    def __init__(self,parent):
        pass

    def log_compare(self,parent):
        import os,filecmp
        logger  = parent.logger
        original= self.subs_f21_path

        # compare all files againts the first one downloaded
        if not filecmp.cmp(original,self.subs_f44_path): logger.error("file %s and %s differs" % original,self.subs_f44_path)

    def log_state(self,parent,propagated):
        logger = parent.logger

        if not os.path.isfile(self.subs_f21_path) : logger.warning("%s not found" % self.subs_f21_path) 
        if not os.path.isfile(self.subs_f44_path) : logger.warning("%s not found" % self.subs_f44_path) 
        logger.warning("propagated = %d" % propagated) 

    def on_message(self,parent):
        import shutil

        logger = parent.logger
        msg    = parent.msg
        root   = parent.currentDir
        relp   = msg.relpath

        logger.info("msg_cclean_f90.py on_message")

        # build all 6 paths of a successfull propagated path

        if relp[0] != '/' : relp = '/' + relp

        self.subs_f21_path = relp                             # subscribe cdlnd_f21
        self.subs_f44_path = relp.replace('/cfr/','/cfile/')  # subscribe cfile_f44

        # propagated count 

        propagated = 0
        if os.path.isfile(self.subs_f44_path) : propagated += 1

        # propagation unfinished ... (or test error ?)
        # retry message screened out of on_message is taken out of retry
        # here we enforce keeping it... to verify propagation again

        if propagated != 1 :
           logger.warning("%s not fully propagated" % relp )
           # if testing
           self.log_state(parent,propagated)
           parent.consumer.sleep_now = parent.consumer.sleep_min
           parent.consumer.msg_to_retry()
           return False

        # ok it is everywhere ... compare files

        self.log_compare(parent)

        # increase coverage for : put under watched dir a different flavor of that file

        watched_dir  = os.path.dirname( self.subs_f21_path)
        watched_file = os.path.basename(self.subs_f21_path)

        os.chdir(watched_dir)

        # pick one test randomly 

        testid =  random.randint(0,3)

        # expand tests

        if   testid == 0 :
                           shutil.copy(watched_file,watched_file +'.S P C')
                           msg.headers['cclean_f90'] = '.S P C'

        elif testid == 1 :
                           os.symlink( watched_file,watched_file +'.slink')
                           msg.headers['cclean_f90'] = '.slink'

        elif testid == 2 :
                           os.link   ( watched_file,watched_file +'.hlink')
                           msg.headers['cclean_f90'] = '.hlink'

        elif testid == 3 :
                           os.rename ( watched_file ,watched_file +'.moved')
                           msg.headers['cclean_f90'] = '.moved'

        logger.debug("extension = %s" % msg.headers['cclean_f90'])

        return True

self.plugin='Msg_Cclean_F90'
