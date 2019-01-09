#!/usr/bin/python3

"""
  Msg_Cclean_F92
  
  plugin that check for finality of each products... should be removed everywhere

  The post_log count should be the same as the original flow test count

"""
import os,stat,time

class Msg_Cclean_F92(object): 

    def __init__(self,parent):
        pass

    def on_message(self,parent):
        import shutil

        logger = parent.logger
        msg    = parent.msg
        root   = parent.currentDir
        relp   = msg.relpath

        logger.info("msg_cclean_f92.py on_message")

        if 'cclean_f91' in msg.headers :
           ext = msg.headers['cclean_f91']
           msg.headers['cclean_f92'] = ext

        else:
           logger.info("msg_log received: %s %s%s topic=%s lag=%g %s" % \
           ( msg.pubtime, msg.baseurl, msg.relpath, msg.topic, msg.get_elapse(), msg.hdrstr ) )
           logger.error("The message received is incorrect not from shovel clean_f91")
           return False


        # build all 3 paths of a successfull propagated path

        if relp[0] != '/' : relp = '/' + relp

        self.subs_f21_path = relp                             # subscribe cdlnd_f21
        self.subs_f44_path = relp.replace('/cfr/','/cfile/')  # subscribe cfile_f44

        # removed count 

        removed = 0
        if not os.path.isfile(self.subs_f44_path    ) : removed += 1
        if not os.path.isfile(self.subs_f44_path+ext) : removed += 1

        # propagation unfinished ... (or test error ?)
        # retry message screened out of on_message is taken out of retry
        # here we enforce keeping it... to verify propagation again

        if removed != 2 :
           logger.warning("%s not fully cleaned up" % relp )
           parent.consumer.sleep_now = parent.consumer.sleep_min
           parent.consumer.msg_to_retry()
           return False

        del msg.headers['cclean_f91']

        return True

self.plugin='Msg_Cclean_F92'
