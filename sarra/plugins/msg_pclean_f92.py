#!/usr/bin/python3

"""
  Msg_Clean_F92
  
  plugin that check for finality of each products... should be removed everywhere

  The post_log count should be the same as the original flow test count

"""
import os,stat,time

class Msg_Clean_F92(object): 

    def __init__(self,parent):
        pass

    def on_message(self,parent):
        import shutil

        logger = parent.logger
        msg    = parent.msg
        root   = parent.currentDir
        relp   = msg.relpath

        logger.info("msg_pclean_f92.py on_message")

        if 'pclean_f91' in msg.headers :
           ext = msg.headers['pclean_f91']

        else:
           logger.info("msg_log received: %s %s%s topic=%s lag=%g %s" % \
               ( msg.pubtime, msg.baseurl, msg.relpath, msg.topic, msg.get_elapse(), msg.hdrstr ) )
           logger.error("The message received is incorrect not from shovel clean_f91")
           return False

        # build all 3 paths of a successfull propagated path

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

        # removed count 

        removed = 0
        if not os.path.exists(self.sarr_f20_path    ) : removed += 1

        if not os.path.exists(self.subs_f30_path    ) : removed += 1
        if not os.path.exists(self.send_f50_path    ) : removed += 1
        if not os.path.exists(self.subs_f60_path    ) : removed += 1
        if not os.path.exists(self.subs_f70_path    ) : removed += 1
        if not os.path.exists(self.subs_f71_path    ) : removed += 1
        if not os.path.exists(self.flow_post_cp     ) : removed += 1

        if not os.path.exists(self.subs_f30_path+ext) : removed += 1
        if not os.path.exists(self.send_f50_path+ext) : removed += 1
        if not os.path.exists(self.subs_f60_path+ext) : removed += 1
        if not os.path.exists(self.subs_f70_path+ext) : removed += 1
        if not os.path.exists(self.subs_f71_path+ext) : removed += 1
        if not os.path.exists(self.flow_post_cp +ext) : removed += 1


        # propagation unfinished ... (or test error ?)
        # retry message screened out of on_message is taken out of retry
        # here we enforce keeping it... to verify propagation again

        if removed != 13 :
           logger.warning("%s not fully cleaned up" % relp )
           # if testing
           # self.log_state(parent,propagated,ext)
           parent.consumer.sleep_now = parent.consumer.sleep_min
           parent.consumer.msg_to_retry()
           parent.msg.isRetry = False
           return False

        msg.headers['pclean_f92'] = ext
        del msg.headers['pclean_f91']

        return True

self.plugin='Msg_Clean_F92'
