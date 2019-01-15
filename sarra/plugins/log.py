#!/usr/bin/python3

"""
  Example plugin that implements logging at all on_* points. 

  plugin log

  This file can contain arbitrary python code, but must include the declaration of a class,
  and the assignment of the class's name to self.plugin
"""

"""

 Mandatory must declare a class with at least one upper case character in the name, 
 as well as the __init__ constructor. Then provide as many routines as needed for 
 the function.

"""
class Log(object):  

    def __init__(self,parent):
        #parent.logger.debug("log initialized")
        pass
          
    def on_start(self,parent):
        """ Runs when the component is started up.
        """
        parent.logger.info("log start %s" % sarra.__version__ )
        return True

    def on_stop(self,parent):
        """ Runs when the component is stopped.
        """
        parent.logger.info("log stop")
        return True

    def on_message(self,parent):
        """ when an sr_post(7) message has been received.  For example, a message has been received
            and additional criteria are being evaluated for download of the corresponding file.  if the on_msg
            script returns false, then it is not downloaded.  (see discard_when_lagging.py, for example,
            which decides that data that is too old is not worth downloading.)
        """
        msg = parent.msg
        parent.logger.info("log message accepted: %s %s%s topic=%s lag=%g %s" % \
           ( msg.pubtime, msg.baseurl, msg.relpath, msg.topic, msg.get_elapse(), msg.hdrstr ) )
        return True
          
    def on_part(self,parent):
        """ Large file transfers are split into parts. Each part is transferred separately.
            When a completed part is received, one can specify additional processing.
            Can process parts of files while the rest is in transit, i.e. for AV.
        """

        # make sure only a part gets logged
        try   :
                if parent.msg.headers['parts'][0] == '1' : return True
        except: pass

        parent.logger.info("log part downloaded to: %s/%s" % ( parent.msg.new_dir, parent.msg.new_file) )
        return True

    def on_file(self,parent):
        """ When the reception of a file has been completed, trigger followup action.
        """

        parent.logger.info("log file downloaded to: %s/%s" % ( parent.msg.new_dir, parent.msg.new_file) )
        return True

    def on_post(self,parent):
        """ when a data source (or sarra) is about to post a message, permit customized
            adjustments of the post. on_part also defaults to post_log, which prints a 
            message whenever a file is to be posted.
        """
        msg = parent.msg
        parent.logger.info("log post notice=%s %s %s headers=%s" % \
            ( msg.pubtime, msg.baseurl, msg.relpath, msg.headers ) )
        return True

    def on_heartbeat(self,parent):
        parent.logger.info("log heartbeat. Sarracenia version is: %s" % sarra.__version__ )
        return True

    def on_watch(self,parent):
        """ when the processing of **sr_watch** events starts (every *sleep* interval) 
            on_watch plugin is invoked. 
        """
        parent.logger.info("log watch." )
        return True
#
# More specialized entry points:
#
#    def on_html_page(self,parent): 
#       """ In **sr_poll**, turns an html page into a python dictionary used to keep in 
#           mind the files already published. The package provide a working example under 
#           plugins/html_page.py.
#       """
#       pass
#
#    def on_line(self,parent): 
#       """ In **sr_poll** a line from the ls on the remote host is read in.
#       """
#       pass
#   
#    def do_download(self,parent):
#       """ to implement additional download protocols.
#           Plugin is called for unknown protocols, so use an on_message routine to switch it.
#           See wget and cp plugins for examples.
#       """
#       pass
#   
#    def do_poll(self, parent): 
#       """ to implement additional polling protocols and processes.
#           replaces built-in poll when declared.
#       """
#       pass
#   
#    def do_send(self,parent): 
#       """ To implement additional sending protocols and processes.
#           replaces built-in sender when declared.
#       """
#       pass
#   

# Mandatory element, assign the value to the case-exact name of the class with the entry points.
self.plugin = 'Log'
