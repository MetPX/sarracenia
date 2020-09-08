#!/usr/bin/python3
"""
  Msg_Cclean_F91
  
  plugin that receives a message from shovel clean_f90 ... for each product... python side
  - it checks if the propagation was ok.
  - it removes the product instances at the watch level
  - it posts the product again (shovel clean_f92 )

  when a product is not fully propagated, it is put in the retry list

  The post_log count should be the same as the original flow test count

"""
import os


class Msg_Cclean_F91(object):
    def __init__(self, parent):
        self.subs_f21_path = None
        self.subs_f44_path = None

    def log_state(self, parent, propagated, ext=None):
        logger = parent.logger

        if not ext:
            if not os.path.isfile(self.subs_f21_path):
                logger.warning("file (%s) not found" % self.subs_f21_path)
            if not os.path.isfile(self.subs_f44_path):
                logger.warning("file (%s) not found" % self.subs_f44_path)
        else:
            if not os.path.isfile(self.subs_f21_path + ext):
                logger.warning("file (%s) not found" % self.subs_f21_path +
                               ext)
            if not os.path.isfile(self.subs_f44_path + ext):
                logger.warning("file (%s) not found" % self.subs_f44_path +
                               ext)
        logger.debug("propagated = %d" % propagated)

    def on_message(self, parent):
        logger = parent.logger
        msg = parent.msg
        root = parent.currentDir
        relp = msg.relpath

        logger.info("msg_pclean_f91.py on_message")

        if 'cclean_f90' in msg.headers:
            ext = msg.headers['cclean_f90']
            msg.headers['cclean_f91'] = ext

        else:
            msg_params = (msg.pubtime, msg.baseurl, msg.relpath, msg.topic,
                          msg.get_elapse(), msg.hdrstr)
            logger.info("msg_log received: %s %s%s topic=%s lag=%g %s" %
                        msg_params)
            logger.error(
                "The message received is incorrect not from shovel cclean_f90")
            return False

        # build all 3 paths of a successfull propagated path
        if relp[0] != '/':
            relp = '/' + relp
        self.subs_f21_path = relp  # subscribe cdlnd_f21
        self.subs_f44_path = relp.replace('/cfr/',
                                          '/cfile/')  # subscribe cfile_f44

        # propagated count
        propagated = 0
        if os.path.isfile(self.subs_f44_path + ext):
            propagated += 1

        # propagation unfinished ... (or test error ?)
        # retry message screened out of on_message is taken out of retry
        # here we enforce keeping it... to verify propagation again
        if propagated != 1:
            logger.warning("propagation not completed for file: %s" % relp)
            # if testing
            self.log_state(parent, propagated, ext)
            parent.consumer.sleep_now = parent.consumer.sleep_min
            parent.consumer.msg_to_retry()
            return False

        # ok it is everywhere ...  # do big cleanup
        try:
            os.unlink(self.subs_f21_path)
        except OSError:
            logger.warning("file (%s) already deleted ?" % self.subs_f21_path)
        try:
            os.unlink(self.subs_f21_path + ext)
        except OSError:
            logger.warning("file (%s) already deleted ?" % self.subs_f21_path +
                           ext)

        del msg.headers['cclean_f90']
        return True


self.plugin = 'Msg_Cclean_F91'
