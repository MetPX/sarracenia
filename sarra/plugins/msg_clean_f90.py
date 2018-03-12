#!/usr/bin/python3

"""
  Msg_Clean_F90
  
  plugin that is used in shovel clean_f90 ... for each product... python side
  - it checks if the propagation was ok.
  - it removes the product instances (for processes that would not remove it)
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

    def on_message(self,parent):
        import shutil

        logger = parent.logger
        msg    = parent.msg
        root   = parent.currentDir
        relp   = msg.relpath

        # build all 6 paths of a successfull propagated path

        if relp[0] != '/' : relp = '/' + relp

        sarr_f20_path = root                             + relp
        subs_f30_path = root + '/downloaded_by_sub_t'    + relp
        # f40 is watch... no file
        send_f50_path = root + '/sent_by_tsource2send'   + relp
        subs_f60_path = root + '/downloaded_by_sub_u'    + relp
        # at f60 there is a post and a poll... no file
        subs_f70_path = root + '/posted_by_srpost_test2' + relp
        subs_f71_path = root + '/recd_by_srpoll_test1'   + relp

        # propagated count 

        propagated = 0
        if os.path.isfile(sarr_f20_path) : propagated += 1
        if os.path.isfile(subs_f30_path) : propagated += 1
        if os.path.isfile(send_f50_path) : propagated += 1
        if os.path.isfile(subs_f60_path) : propagated += 1
        if os.path.isfile(subs_f70_path) : propagated += 1
        if os.path.isfile(subs_f71_path) : propagated += 1

        #if not os.path.isfile(sarr_f20_path) : logger.warning("%s not found" % sarr_f20_path) 
        #if not os.path.isfile(subs_f30_path) : logger.warning("%s not found" % subs_f30_path) 
        #if not os.path.isfile(send_f50_path) : logger.warning("%s not found" % send_f50_path) 
        #if not os.path.isfile(subs_f60_path) : logger.warning("%s not found" % subs_f60_path) 
        #if not os.path.isfile(subs_f70_path) : logger.warning("%s not found" % subs_f70_path) 
        #if not os.path.isfile(subs_f70_path) : logger.warning("%s not found" % subs_f71_path) 
        #logger.warning("propagated = %d" % propagated) 

        # propagation unfinished ... (or test error ?)
        # retry message screened out of on_message is taken out of retry
        # here we enforce keeping it... to verify propagation again

        if propagated != 6 :
           logger.warning("%s not fully propagated" % relp )
           parent.consumer.msg_to_retry()
           return False

        # ok it is everywhere ... it worked

        # MG SUGGESTION
        # some integrity testing of the product in all these paths
        # could be performed here...  WARN FOR DIFFERENCE ONLY ...
        # but do not return False ... NOT TO COMPROMISE WITH FLOW TEST COUNT

        # remove unneeded file

        os.unlink(sarr_f20_path)   # sarra of dd.weather download deleted
        #os.unlink(subs_f30_path)  watch     its path
        #os.unlink(send_f50_path)  sender    of  watch announcement
        #os.unlink(subs_f60_path)  subscribe to sender reannouncement
        os.unlink(subs_f70_path)   # sr_post file deleted
        os.unlink(subs_f71_path)   # sr_poll file deleted

        # =================================================
        # expanded converage test
        # watch f30 / sender f50 / subscribe f60
        # pick one of copy (filename_with_space), slink, hlink, mv
        # the original file is mv... or delete
        # =================================================

        watched_dir  = os.path.dirname( subs_f30_path)
        watched_file = os.path.basename(subs_f30_path)

        os.chdir(watched_dir)

        # pick one test randomly 

        testid =  random.randint(0,3)

        if   testid == 0 : shutil.copy(watched_file,watched_file +'.S P C')
        elif testid == 1 : os.symlink( watched_file,watched_file +'.slink')
        elif testid == 2 : os.link   ( watched_file,watched_file +'.hlink')
        elif testid == 3 : os.rename ( watched_file,watched_file +'.moved')

        if   testid == 0 : msg.headers['clean_f90'] = '.S P C'
        elif testid == 1 : msg.headers['clean_f90'] = '.slink'
        elif testid == 2 : msg.headers['clean_f90'] = '.hlink'
        elif testid == 3 : msg.headers['clean_f90'] = '.moved'

        if   testid != 3 : os.unlink(subs_f30_path)

        #logger.warning("OK %s" % msg.headers['clean_f90'])

        # IF the flow test number is N... 
        # the watched events should be N * ( 1 original + 1 test + 1 remove original + 1 remove test)
        # so total of 4 * N
        
        return True

self.plugin='Msg_Clean_F90'
