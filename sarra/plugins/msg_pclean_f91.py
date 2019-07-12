#!/usr/bin/python3

"""
  Msg_Clean_F91
  
  plugin that receives a message from shovel clean_f90 ... for each product... python side
  - it checks if the propagation was ok.
  - it removes the product instances at the watch level
  - it posts the product again (shovel clean_f92 )

  when a product is not fully propagated, it is put in the retry list

  The post_log count should be the same as the original flow test count

"""
import os


class Msg_Clean_F91(object):
    def __init__(self, parent):
        self.sarr_f20_path = None
        self.subs_f30_path = None
        self.send_f50_path = None
        self.subs_f60_path = None
        self.subs_f70_path = None
        self.subs_f71_path = None
        self.flow_post_cp = None

    def log_state(self, parent, propagated, ext):
        logger = parent.logger

        if not os.path.exists(self.subs_f30_path + ext):
            logger.debug("file (%s) not found" % self.subs_f30_path + ext)
        if not os.path.exists(self.send_f50_path + ext):
            logger.debug("file (%s) not found" % self.send_f50_path + ext)
        if not os.path.exists(self.subs_f60_path + ext):
            logger.debug("file (%s) not found" % self.subs_f60_path + ext)
        if not os.path.exists(self.subs_f70_path + ext):
            logger.debug("file (%s) not found" % self.subs_f70_path + ext)
        if not os.path.exists(self.subs_f71_path + ext):
            logger.debug("file (%s) not found" % self.subs_f71_path + ext)
        if not os.path.exists(self.flow_post_cp + ext):
            logger.debug("file (%s) not found" % self.flow_post_cp + ext)

    def on_message(self, parent):

        logger = parent.logger
        msg = parent.msg
        root = parent.currentDir
        relp = msg.relpath

        logger.info("msg_pclean_f91.py on_message")

        if 'pclean_f90' in msg.headers:
            ext = msg.headers['pclean_f90']
        else:
            msg_params = (msg.pubtime, msg.baseurl, msg.relpath, msg.topic, msg.get_elapse(), msg.hdrstr)
            logger.info("msg_log received: %s %s%s topic=%s lag=%g %s" % msg_params)
            logger.error("message received not from shovel clean_f90")
            return False

        # build all 3 paths of a successful propagated path
        if relp[0] != '/': relp = '/' + relp

        self.sarr_f20_path = root + relp  # sarra
        self.subs_f30_path = root + '/downloaded_by_sub_amqp' + relp  # subscribe t_sub
        # f40 is watch... no file
        self.send_f50_path = root + '/sent_by_tsource2send' + relp  # sender
        self.subs_f60_path = root + '/downloaded_by_sub_u' + relp  # subscribe u_sftp_f60
        # at f60 there is a post and a poll... no file
        self.subs_f70_path = root + '/posted_by_srpost_test2' + relp  # subscribe ftp_f70
        self.subs_f71_path = root + '/recd_by_srpoll_test1' + relp  # subscribe q_f71
        self.flow_post_cp = root + '/posted_by_shim' + relp  # flow_post cp

        # propagated count
        propagated = 0
        if os.path.exists(self.subs_f30_path + ext):
            propagated += 1
        if os.path.exists(self.send_f50_path + ext):
            propagated += 1
        if os.path.exists(self.subs_f60_path + ext):
            propagated += 1
        if os.path.exists(self.subs_f70_path + ext):
            propagated += 1
        if os.path.exists(self.subs_f71_path + ext):
            propagated += 1
        if os.path.exists(self.flow_post_cp + ext):
            propagated += 1

        # propagation unfinished ... (or test error ?)
        # retry message screened out of on_message is taken out of retry
        # here we enforce keeping it... to verify propagation again
        if propagated != 6:
            logger.error("propagation not completed for file: %s" % relp)
            # if testing
            self.log_state(parent, propagated, ext)
            return False

        # ok it is everywhere ...  delete original
        try:
            os.unlink(self.sarr_f20_path)
        except OSError:
            logger.debug("%s already deleted ?" % self.sarr_f20_path)
        try:
            os.unlink(self.subs_f30_path)
        except OSError:
            if ext != '.moved':
                logger.debug("%s already deleted ?" % self.subs_f30_path)

        # by deleting self.subs_f30_path, watch should propagate the removal of theses two.
        # os.unlink( self.subs_f50_path)
        # os.unlink( self.subs_f60_path)
        try:
            os.unlink(self.subs_f70_path)
        except OSError:
            logger.debug("%s already deleted ?" % self.subs_f70_path)
        try:
            os.unlink(self.subs_f71_path)
        except OSError:
            logger.debug("%s already deleted ?" % self.subs_f71_path)
        try:
            os.unlink(self.flow_post_cp)
        except OSError:
            logger.debug("%s already deleted ?" % self.flow_post_cp)

        # delete original with extension where it makes sense
        # extension file was generated at next level
        # os.unlink( self.sarr_f20_path)
        try:
            os.unlink(self.subs_f30_path + ext)
        except OSError:
            logger.debug("%s already deleted ?" % self.subs_f30_path + ext)

        # by deleting self.subs_f30_path+ext, watch should propagate the removal of theses two.
        # os.unlink( self.subs_f50_path+ext)
        # os.unlink( self.subs_f60_path+ext)
        try:
            os.unlink(self.subs_f70_path + ext)
        except OSError:
            logger.debug("%s already deleted ?" % self.subs_f70_path + ext)
        try:
            os.unlink(self.subs_f71_path + ext)
        except OSError:
            logger.debug("%s already deleted ?" % self.subs_f71_path + ext)
        try:
            os.unlink(self.flow_post_cp + ext)
        except OSError:
            logger.debug("%s already deleted ?" % self.flow_post_cp + ext)

        msg.headers['pclean_f91'] = ext
        del msg.headers['pclean_f90']
        return True


self.plugin = 'Msg_Clean_F91'
