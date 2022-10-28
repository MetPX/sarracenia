import json
import logging
from sarracenia.flowcb import FlowCB
import subprocess

logger = logging.getLogger(__name__)


class Run(FlowCB):
    """
       sample usages:

       # run a script on every file downloaded
       run_work_item ls -al
       callback run

       module to run scripts or binary (non-python) whenever you need to.  
       typically use would be to fetch files for processing by watch.

       options:

       run_gather  

              using flowCallbackPrepend places it at the front of the flowcb list.
              ... script to run before gather (so gather.file will pick it up.)
 
       run_accept ...

       run_accept_item ...
               item scripts, instead of being invoked to replace all processing at a given time,
               are invoked per item in the worklist. At the accept phase, these are in worklist.incoming.
       
       run_work
               invoked for the whole phase.

       run_work_item
                a script invoked to treat every file already transferred by going through the worklist.ok


       run_post

       run_start

       run_stop

    """
    def __init__(self, options):

        # FIXME: should a logging module have a logLevel setting?
        #        just put in a cookie cutter for now...
        if hasattr(options, 'logLevel'):
            logger.setLevel(getattr(logging, options.logLevel.upper()))
        else:
            logger.setLevel(logging.INFO)

        self.o = options
        self.o.add_option('run_gather', 'str')
        self.o.add_option('run_accept', 'str')
        self.o.add_option('run_accept_item', 'str')
        self.o.add_option('run_work', 'str')
        self.o.add_option('run_work_item', 'str')
        self.o.add_option('run_post', 'str')
        self.o.add_option('run_start', 'str')
        self.o.add_option('run_stop', 'str')
        self.o.add_option('run_housekeeping', 'str')

    def run_script(self, script):
        try:
            subprocess.run(script, check=True)
        except Exception as err:
            logging.error("subprocess.run failed err={}".format(err))
            logging.debug("Exception details:", exc_info=True)

    def gather(self):
        """
           FIXME: this does not make sense. need to figure out how to get the 
           messages back from the script, perhaps using a json file reader?
        """
        if hasattr(self.o,
                   'run_gather') and self.o.run_gather is not None:
            self.run_script(self.o.run_gather)
        return []

    def after_accept(self, worklist):
        """
           FIXME: this does not make sense. need to figure out how to feed the
           files to the script... command line argument? 
        """
        if hasattr(self.o,
                   'run_accept') and self.o.run_accept:
            self.run_script(self.o.run_accept)

        if hasattr(self.o, 'run_accept_item' ) and self.o.run_accept_item:
            for m in worklist.incoming:
                cmd = self.o.run_accept_item.split()
                cmd.append( f"{m['new_dir']}/{m['new_file']}" )
                try:
                    p = subprocess.Popen( cmd )
                    p.wait()
                    if p.returncode == 0:
                        logger.info( f"ran {cmd} successfully")
                    else:
                        logger.error( f"ran {cmd}: output: {o}")

                except Exception as ex:
                    logger.error( f"problem running {cmd}: {ex}" )

    def after_work(self, worklist):
        """
           FIXME: this does not make sense. need to figure out how to feed the
           files to the script... command line argument? 
        """
        if hasattr(self.o, 'run_work') and self.o.run_work is not None:
            self.run_script(self.o.run_work)

        if hasattr(self.o, 'run_work_item' ) and self.o.run_work_item is not None:
            for m in worklist.ok:
                cmd = self.o.run_work_item.split()
                cmd.append( f"{m['new_dir']}/{m['new_file']}" )
                try:
                    p = subprocess.Popen( cmd )
                    p.wait()
                    if p.returncode == 0:
                        logger.info( f"ran {cmd} successfully")
                    else:
                        logger.error( f"ran {cmd}: output: {o}")

                except Exception as ex:
                    logger.error( f"problem running {cmd}: {ex}" )

    def post(self, worklist):
        """
           FIXME: this does not make sense. need to figure out how to feed the
           messages to the script... command line argument? 
        """
        if hasattr(self.o, 'run_post') and self.o.run_post is not None:
            self.run_script(self.o.run_post)

    def on_start(self):
        if hasattr(self.o, 'run_start') and self.o.run_start is not None:
            self.run_script(self.o.run_start)

    def on_stop(self):
        if hasattr(self.o, 'run_stop') and self.o.run_stop is not None:
            self.run_script(self.o.run_stop)

    def housekeeping(self):
        if hasattr(self.o, 'run_housekeeping'
                   ) and self.o.run_housekeeping is not None:
            self.run_script(self.o.run_housekeeping)
