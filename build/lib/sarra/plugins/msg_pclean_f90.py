#!/usr/bin/python3

"""
  Msg_Pclean_F90
  
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

class Msg_Pclean_F90(object): 

    def __init__(self,parent):
        pass

    def log_compare(self,parent):
        import os,filecmp
        logger  = parent.logger
        original= self.sarr_f20_path

        # compare all files againts the first one downloaded
        if not filecmp.cmp(original,self.subs_f30_path): logger.error("file %s and %s differs" % (original,self.subs_f30_path))
        if not filecmp.cmp(original,self.send_f50_path): logger.error("file %s and %s differs" % (original,self.send_f50_path))
        if not filecmp.cmp(original,self.subs_f60_path): logger.error("file %s and %s differs" % (original,self.subs_f60_path))
        if not filecmp.cmp(original,self.subs_f70_path): logger.error("file %s and %s differs" % (original,self.subs_f70_path))
        if not filecmp.cmp(original,self.subs_f71_path): logger.error("file %s and %s differs" % (original,self.subs_f71_path))
        if not filecmp.cmp(original,self.flow_post_cp ): logger.error("file %s and %s differs" % (original,self.flow_post_cp ))

    def log_state(self,parent,propagated):
        logger = parent.logger

        if not os.path.exists(self.sarr_f20_path) : logger.warning("%s not found" % self.sarr_f20_path) 
        if not os.path.exists(self.subs_f30_path) : logger.warning("%s not found" % self.subs_f30_path) 
        if not os.path.exists(self.send_f50_path) : logger.warning("%s not found" % self.send_f50_path) 
        if not os.path.exists(self.subs_f60_path) : logger.warning("%s not found" % self.subs_f60_path) 
        if not os.path.exists(self.subs_f70_path) : logger.warning("%s not found" % self.subs_f70_path) 
        if not os.path.exists(self.subs_f71_path) : logger.warning("%s not found" % self.subs_f71_path) 
        if not os.path.exists(self.flow_post_cp ) : logger.warning("%s not found" % self.flow_post_cp ) 
        logger.warning("propagated = %d" % propagated) 

    def is_propagated(self,parent,path):
        if not os.path.exists(path) : return False
        now    = time.time()
        elapse = now - os.stat(path)[stat.ST_MTIME]
        if elapse > 10 : return True
        return False

    def on_message(self,parent):
        import shutil

        logger = parent.logger
        msg    = parent.msg
        root   = parent.currentDir
        relp   = msg.relpath

        logger.info("msg_pclean_f90.py on_message")

        # build all 6 paths of a successfull propagated path

        if relp[0] != '/' : relp = '/' + relp

        self.sarr_f20_path = root                             + relp   # sarra
        self.subs_f30_path = root + '/downloaded_by_sub_t'    + relp   # subscribe t_sub
        # f40 is watch... no file
        self.send_f50_path = root + '/sent_by_tsource2send'   + relp   # sender
        self.subs_f60_path = root + '/downloaded_by_sub_u'    + relp   # subscribe u_sftp_f60
        # at f60 there is a post and a poll... no file
        self.subs_f70_path = root + '/posted_by_srpost_test2' + relp   # subscribe ftp_f70
        self.subs_f71_path = root + '/recd_by_srpoll_test1'   + relp   # subscribe q_f71
        self.flow_post_cp  = root + '/posted_by_shim'         + relp   # flow_post cp

        # propagated count 

        propagated = 0
        if self.is_propagated(parent,self.sarr_f20_path) : propagated += 1
        if self.is_propagated(parent,self.subs_f30_path) : propagated += 1
        if self.is_propagated(parent,self.send_f50_path) : propagated += 1
        if self.is_propagated(parent,self.subs_f60_path) : propagated += 1
        if self.is_propagated(parent,self.subs_f70_path) : propagated += 1
        if self.is_propagated(parent,self.subs_f71_path) : propagated += 1
        if self.is_propagated(parent,self.flow_post_cp ) : propagated += 1

        # propagation unfinished ... (or test error ?)
        # retry message screened out of on_message is taken out of retry
        # here we enforce keeping it... to verify propagation again

        if propagated != 7 :
           logger.warning("%s not fully propagated" % relp )
           # if testing
           self.log_state(parent,propagated)
           parent.consumer.sleep_now = parent.consumer.sleep_min
           parent.consumer.msg_to_retry()
           parent.msg.isRetry = False
           return False

        # ok it is everywhere ... compare files

        self.log_compare(parent)

        # increase coverage for : put under watched dir a different flavor of that file

        watched_dir  = os.path.dirname( self.subs_f30_path)
        watched_file = os.path.basename(self.subs_f30_path)

        os.chdir(watched_dir)

        # pick one test randomly 

        testid =  random.randint(0,3)

        # avoid space until flow_post.sh is corrected
        testid =  random.randint(0,2) + 1

        # expand tests

        if   testid == 0 :
                           shutil.copy(watched_file,watched_file +'.S P C')
                           msg.headers['pclean_f90'] = '.S P C'

        elif testid == 1 :
                           os.symlink( watched_file,watched_file +'.slink')
                           msg.headers['pclean_f90'] = '.slink'

        elif testid == 2 :
                           os.link   ( watched_file,watched_file +'.hlink')
                           msg.headers['pclean_f90'] = '.hlink'

        elif testid == 3 :
                           os.rename ( watched_file ,watched_file +'.moved')
                           msg.headers['pclean_f90'] = '.moved'

        del msg.headers['toolong']

        return True

self.plugin='Msg_Pclean_F90'
