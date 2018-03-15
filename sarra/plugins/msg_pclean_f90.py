#!/usr/bin/python3

"""
  Msg_Clean_F90
  
  plugin that is used in shovel clean_f90 ... for each product... python side
  - it checks if the propagation was ok.
  - it randomly set a test in the watch f40.conf for propagation
  - it remove the original product ... which is propagated too
  - it posts the product again (more test in shovel clean_f91)

  when a product is not fully propagated, it is put in the retry list

  The post_log count should be the same as the original flow test count

  The posted message contains a tag in the header for the test performed
  which is the extension used for the test

"""
import os,stat,time

class Msg_Clean_F90(object): 

    def __init__(self,parent):
        pass

    def log_state(self,parent,propagated):
        logger = parent.logger

        if not os.path.isfile(self.sarr_f20_path) : logger.warning("%s not found" % self.sarr_f20_path) 
        if not os.path.isfile(self.subs_f30_path) : logger.warning("%s not found" % self.subs_f30_path) 
        if not os.path.isfile(self.send_f50_path) : logger.warning("%s not found" % self.send_f50_path) 
        if not os.path.isfile(self.subs_f60_path) : logger.warning("%s not found" % self.subs_f60_path) 
        if not os.path.isfile(self.subs_f70_path) : logger.warning("%s not found" % self.subs_f70_path) 
        if not os.path.isfile(self.subs_f70_path) : logger.warning("%s not found" % self.subs_f71_path) 
        logger.warning("propagated = %d" % propagated) 

    def on_message(self,parent):
        import shutil

        logger = parent.logger
        msg    = parent.msg
        root   = parent.currentDir
        relp   = msg.relpath

        # build all 6 paths of a successfull propagated path

        if relp[0] != '/' : relp = '/' + relp

        self.sarr_f20_path = root                             + relp
        self.subs_f30_path = root + '/downloaded_by_sub_t'    + relp
        # f40 is watch... no file
        self.send_f50_path = root + '/sent_by_tsource2send'   + relp
        self.subs_f60_path = root + '/downloaded_by_sub_u'    + relp
        # at f60 there is a post and a poll... no file
        self.subs_f70_path = root + '/posted_by_srpost_test2' + relp
        self.subs_f71_path = root + '/recd_by_srpoll_test1'   + relp

        # propagated count 

        propagated = 0
        if os.path.isfile(self.sarr_f20_path) : propagated += 1
        if os.path.isfile(self.subs_f30_path) : propagated += 1
        if os.path.isfile(self.send_f50_path) : propagated += 1
        if os.path.isfile(self.subs_f60_path) : propagated += 1
        if os.path.isfile(self.subs_f70_path) : propagated += 1
        if os.path.isfile(self.subs_f71_path) : propagated += 1


        # propagation unfinished ... (or test error ?)
        # retry message screened out of on_message is taken out of retry
        # here we enforce keeping it... to verify propagation again

        if propagated != 6 :
           logger.warning("%s not fully propagated" % relp )
           # if testing
           #self.log_state(parent,propagated)
           parent.consumer.msg_to_retry()
           return False

        # ok it is everywhere ...
        # increase coverage for : watch f30 / sender f50 / subscribe f60

        watched_dir  = os.path.dirname( self.subs_f30_path)
        watched_file = os.path.basename(self.subs_f30_path)

        os.chdir(watched_dir)

        # pick one test randomly 

        testid =  random.randint(0,3)

        # make sure each has 2 posts for an equal post_count

        if   testid == 0 :
                           shutil.copy(watched_file,watched_file +'.S P C')
                           msg.headers['clean_f90'] = '.S P C'

        elif testid == 1 :
                           os.symlink( watched_file,watched_file +'.slink')
                           msg.headers['clean_f90'] = '.slink'

        elif testid == 2 :
                           os.link   ( watched_file,watched_file +'.hlink')
                           msg.headers['clean_f90'] = '.hlink'

        elif testid == 3 :
                           os.rename ( watched_file,watched_file +'.moved')
                           msg.headers['clean_f90'] = '.moved'

        return True

self.plugin='Msg_Clean_F90'
