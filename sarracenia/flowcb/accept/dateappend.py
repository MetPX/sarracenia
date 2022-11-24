"""
Plugin dateappend.py:
    This is an  example of the usage of after_accept script
    to rename the product when it is downloaded
    It adds a '_datetime' to the name of the product

    unlikely to be useful to others, except as example.
    note that, in the case of retries, the date will be appended multiple times.
    
    This is for diagnosing problems with data pumps, identifying feed failures and retries.

Example:
    takes input name  : ./SK/s0000684_f.xml
    add datetimestamp : ./SK/s0000684_f.xml_20221022080652
    retries: /SK/s0000684_f.xml_20221022080652_20221022081403, ./SK/s0000684_f.xml_20221022080652_20221022081403_20221022081508

Usage:
    callback accept.dateappend

    if installing where the plugin is not from the package itself, invocation is:

    flowcallback dateappend.Dateappend


"""
import logging
import sys, os, os.path, time, stat
from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)

class Dateappend(FlowCB):
    def __init__(self, options):
        self.o = options
        logger.info('loaded ok')

    def after_accept(self, worklist):

        for message in worklist.incoming:
            datestr = time.strftime('_%Y%m%d%H%M%S', time.localtime())
            message['new_file'] += datestr
