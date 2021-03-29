import json
import logging
from sarracenia.flowcb import FlowCB
from sarracenia.flowcb.gather import msg_dumps
import subprocess

logger = logging.getLogger(__name__)


class Script(FlowCB):
    """
       usage:

       flowcb_prepend sarracenia.flowcb.script.Script

       module to run scripts or binary (non-python) whenever you need to.  
       typically use would be to fetch files for processing by watch.

       options:

       script_gather  

              using flowcb_prepend places it at the front of the flowcb list.
              ... script to run before gather (so gather.file will pick it up.)
 
       script_filter ...

       script_work

       script_post

       script_start

       script_stop

    """
    def __init__(self, options):

        # FIXME: should a logging module have a logLevel setting?
        #        just put in a cookie cutter for now...
        if hasattr(options, 'logLevel'):
            logger.setLevel(getattr(logging, options.logLevel.upper()))
        else:
            logger.setLevel(logging.INFO)

        self.o = options
        self.o.add_option( 'script_gather', 'str' )
        self.o.add_option( 'script_filter', 'str' )
        self.o.add_option( 'script_work', 'str' )
        self.o.add_option( 'script_post', 'str' )
        self.o.add_option( 'script_start', 'str' )
        self.o.add_option( 'script_stop', 'str' )
        self.o.add_option( 'script_housekeeping', 'str' )

    def run_script( self, script ):
        try: 
            subprocess.run( self.o.script_gather, check=True )
        except Exception as err:
            logging.error("subprocess.run failed err={}".format(err))
            logging.debug("Exception details:", exc_info=True)


    def gather(self ):
        if hasattr( self.o, 'script_gather') and self.o.script_gather is not None :
            self.run_script( self.o.script_gather )
        return []

    def after_accept(self, worklist):
        if hasattr( self.o, 'script_filter') and self.o.script_filter is not None :
            self.run_script( self.o.script_filter )

    def after_work(self, worklist):
        if hasattr( self.o, 'script_work') and self.o.script_work is not None :
            self.run_script( self.o.script_work )

    def post(self, worklist):
        if hasattr( self.o, 'script_post') and self.o.script_post is not None :
            self.run_script( self.o.script_post )

    def on_start(self):
        if hasattr( self.o, 'script_start') and self.o.script_start is not None :
            self.run_script( self.o.script_start )

    def on_stop(self):
        if hasattr( self.o, 'script_stop') and self.o.script_stop is not None :
            self.run_script( self.o.script_stop )

    def housekeeping(self):
        if hasattr( self.o, 'script_housekeeping') and self.o.script_housekeeping is not None :
            self.run_script( self.o.script_housekeeping )

