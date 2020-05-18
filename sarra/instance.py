

import copy
import logging
import logging.handlers
import os
from sarra.tmpc import TMPC
from sarra.tmpc.amqp import AMQP
import sys
import time

import appdirs
import sarra.config 
from sarra.audit import Audit
from sarra.flow.shovel import Shovel

from urllib.parse import urlparse,urlunparse

class RedirectedTimedRotatingFileHandler( logging.handlers.TimedRotatingFileHandler ):

    def doRollover(self):
        super().do_rollover()

        if sys.platform != 'win32' :
            os.dup2( self.stream.fileno(), 1 )
            os.dup2( self.stream.fileno(), 2 )
        

def instance():
    """
      Main element to run a single flow instance.  it parses the command line arguments twice.
      the first pass, is to initialize the log file and debug level, and select the configuration file to parse.
      Once the log file is set, and output & error re-direction is in place, the second pass begins:

      The configuration files are parsed, and then the options are parsed a second time to act
      as overrides to the configuration file content.
      
      As all process management is handled by sr.py, the *action* here is not parsed, but always either
      *start* (daemon) or *foreground* (interactive)

    """
    logger = logging.getLogger()
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.DEBUG)
    logger.setLevel( logging.INFO )
     
    default_cfg_dir = appdirs.user_config_dir( 
        sarra.config.Config.appdir_stuff['appname'], 
        sarra.config.Config.appdir_stuff['appauthor']  )
    
    cfg_preparse=sarra.config.Config( \
        { 
           'accept_unmatch':False, 'exchange':None, 'inline':False, 'inline_encoding':'guess'
        } )
     
    cfg_preparse.parse_file( default_cfg_dir + os.sep + "default.conf")
    cfg_preparse.parse_args()
    cfg_preparse.dump()
     
    if cfg_preparse.action not in [ 'foreground', 'start' ]:
        logger.error( 'action must be one of: foreground or start' )
        return

    logger.info('instance 3')
    if cfg_preparse.debug:
         loglevel = logging.DEBUG
    elif hasattr(cfg_preparse,'loglevel'):
        llk = { 'none': logging.NOTSET, 'debug':logging.debug, 'info':logging.info, 'warning': logging.WARNING, 'error':logging.ERROR, 'critical':logging.CRITICAL }
        ll = cfg_preparse.loglevel.lower()
        loglevel =  llk[ll]
    else:
        loglevel = logging.INFO
     
    if not hasattr(cfg_preparse,'no') and not (cfg_preparse.action == 'foreground'):
        logger.critical('need an instance number to run.')
        return
     
    if len(cfg_preparse.configurations) > 1 :
        logger.critical("can only run one configuration in an instance" ) 
        return
     
    logger.info('instance 4')


    # FIXME: do we put explicit error handling here for bad input?
    #        probably worth exploring.
    #
    lr_when=cfg_preparse.lr_when
    if ( type(cfg_preparse.lr_interval) == str ) and ( cfg_preparse.lr_interval[-1] in 'mMhHdD' ):
        lr_when = cfg_preparse.lr_interval[-1]
        lr_interval= int( float(cfg_preparse.lr_interval[:-1]))
    else:
        lr_interval= int( float(cfg_preparse.lr_interval) )

    if type(cfg_preparse.lr_backupCount) == str :
       lr_backupCount= int( float(cfg_preparse.lr_backupCount))
    else: 
       lr_backupCount= cfg_preparse.lr_backupCount

    if ( 'audit' == cfg_preparse.configurations[0] ):
       config=None
       component='audit'
    elif (not os.sep in cfg_preparse.configurations[0]):
        logger.critical("configuration should be of the form component%sconfiguration" % os.sep )
        return
    else:
       component, config = cfg_preparse.configurations[0].split(os.sep) 
     
    logger.info('instance 5')
    # init logs here. need to know instance number and configuration and component before here.
    if cfg_preparse.action == 'start':
        logfilename = sarra.config.get_log_filename( component, config, cfg_preparse.no )
        print('logfilename= %s' % logfilename )
        os.makedirs(os.path.dirname(logfilename), exist_ok=True)

        log_format = '%(asctime)s [%(levelname)s] %(message)s'
        if logging.getLogger().hasHandlers():
            for h in logging.getLogger().handlers:
                h.close()
                logging.getLogger().removeHandler(h)
        logger = logging.getLogger()
        logger.setLevel(loglevel)

        handler = RedirectedTimedRotatingFileHandler(logfilename, 
            when=lr_when, interval=lr_interval, backupCount=lr_backupCount)
        handler.setFormatter(logging.Formatter(log_format))

        logger.addHandler(handler) 

        if hasattr(cfg_preparse, 'chmod_log'):
            if type(cfg_preparse.chmod) == str:
                mode = int( cfg_preparse.chmod_log, base=8 )
            else:
                mode = cfg_preparse.chmod_log

            os.chmod(logfilename, mode )
        if sys.platform != 'win32' :
            os.dup2( handler.stream.fileno(), 1 )
            os.dup2( handler.stream.fileno(), 2 )

    else:
        logger.setLevel(loglevel)
 
    logger.info('instance 6')
     
    if cfg_preparse.action == 'audit':
        logger.error('hoho!')
        auditor = Audit()
        auditor.run()

    else:
        logger.info('instance 7: one_config: %s / %s ' % (component, config ))
        cfg=sarra.config.one_config( component, config, TMPC.default_props() )
        logger.info('instance 8: one_config result: %s ' % (cfg))
        cfg.dump()
        s = Shovel( cfg )                
        s.run()

     
if __name__ == '__main__':
    instance()

