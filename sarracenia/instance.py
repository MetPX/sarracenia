#!/usr/bin/env python3

# This file is part of Sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2020
#

import copy
import logging
import logging.handlers
import os
import pathlib
from sarracenia.moth import Moth
import signal
import sys
import time

from sarracenia import user_config_dir
import sarracenia.config
from sarracenia.flow import Flow

from urllib.parse import urlparse, urlunparse

logger = logging.getLogger(__name__)


class RedirectedTimedRotatingFileHandler(
        logging.handlers.TimedRotatingFileHandler):
    def doRollover(self):
        super().doRollover()

        if sys.platform != 'win32':
            os.dup2(self.stream.fileno(), 1)
            os.dup2(self.stream.fileno(), 2)


class instance:
    """
       Process management for a single flow instance.
       start and stop instances.

       this is the main entry point launched from the sr3 cli, with arguments for it to turn into a specific configuration.
    """
    def __init__(self):
        self.running_instance = None
        original_sigint = signal.getsignal(signal.SIGINT)

    def stop_signal(self, signum, stack):
        logging.info('signal %d received' % signum)
        self.running_instance.please_stop()

    def start(self):
        """
          Main element to run a single flow instance. It parses the command line arguments twice.
          the first pass, is to initialize the log file and debug level, and select the configuration file to parse.
          Once the log file is set, and output & error re-direction is in place, the second pass begins:
    
          The configuration files are parsed, and then the options are parsed a second time to act
          as overrides to the configuration file content.
          
          As all process management is handled by sr.py, the *action* here is not parsed, but always either
          *start* (daemon) or *foreground* (interactive)
    
        """
        global logger

        logging.basicConfig(
            format=
            '%(asctime)s [%(levelname)s] %(process)d %(name)s %(funcName)s %(message)s',
            level=logging.INFO)

        # FIXME: honour SR_ variable for moving preferences...
        default_cfg_dir = sarracenia.user_config_dir(
            sarracenia.config.Config.appdir_stuff['appname'],
            sarracenia.config.Config.appdir_stuff['appauthor'])

        cfg_preparse=sarracenia.config.Config( \
            {
               'acceptUnmatched':False, 'exchange':None, 'inline':False, 'inlineEncoding':'guess', 'logStdout': False,
            } )

        defconfig = default_cfg_dir + os.sep + "default.conf"
        if os.path.exists(defconfig):
            cfg_preparse.parse_file(defconfig)
        cfg_preparse.parse_args()

        #cfg_preparse.dump()

        if cfg_preparse.action not in ['foreground', 'start']:
            logger.error('action must be one of: foreground or start')
            return

        if cfg_preparse.debug:
            logLevel = logging.DEBUG
        elif hasattr(cfg_preparse, 'logLevel'):
            logLevel = getattr(logging, cfg_preparse.logLevel.upper())
        else:
            logLevel = logging.INFO

        logger.setLevel(logLevel)

        if not hasattr(cfg_preparse,
                       'no') and not (cfg_preparse.action == 'foreground'):
            logger.critical('need an instance number to run.')
            return

        if (len(cfg_preparse.configurations) > 1 ) and \
           ( cfg_preparse.configurations[0].split(os.sep)[0] != 'post' ):
            logger.critical("can only run one configuration in an instance")
            return

        if (not os.sep in cfg_preparse.configurations[0]):
            component = 'flow'
            config = cfg_preparse.configurations[0]
        else:
            component, config = cfg_preparse.configurations[0].split(os.sep)

        cfg_preparse = sarracenia.config.one_config(component, config)

        # FIXME: do we put explicit error handling here for bad input?
        #        probably worth exploring.
        #
        lr_when = 'midnight'
        if (type(cfg_preparse.logRotateInterval) == str) and (
                cfg_preparse.logRotateInterval[-1] in 'mMhHdD'):
            lr_when = cfg_preparse.logRotateInterval[-1]
            logRotateInterval = int(float(cfg_preparse.logRotateInterval[:-1]))
        else:
            logRotateInterval = int(float(cfg_preparse.logRotateInterval))

        if type(cfg_preparse.logRotateCount) == str:
            logRotateCount = int(float(cfg_preparse.logRotateCount))
        else:
            logRotateCount = cfg_preparse.logRotateCount

        # init logs here. need to know instance number and configuration and component before here.
        if cfg_preparse.action == 'start' and not cfg_preparse.logStdout:
            if cfg_preparse.statehost:
                hostdir = cfg_preparse.hostdir
            else:
                hostdir = None

            logfilename = sarracenia.config.get_log_filename(
                hostdir, component, config, cfg_preparse.no)

            #print('logfilename= %s' % logfilename )
            dir_not_there = not os.path.exists(os.path.dirname(logfilename))
            while dir_not_there:
                try:
                    os.makedirs(os.path.dirname(logfilename), exist_ok=True)
                    dir_not_there = False
                except FileExistsError:
                    dir_not_there = False
                except Exception as ex:
                    logging.error( "makedirs {} failed err={}".format(os.path.dirname(logfilename),ex))
                    logging.debug("Exception details:", exc_info=True)
                    os.sleep(1)

            log_format = '%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s'
            if logging.getLogger().hasHandlers():
                for h in logging.getLogger().handlers:
                    h.close()
                    logging.getLogger().removeHandler(h)
            logger = logging.getLogger()
            logger.setLevel(logLevel)

            handler = RedirectedTimedRotatingFileHandler(
                logfilename,
                when=lr_when,
                interval=logRotateInterval,
                backupCount=logRotateCount)
            handler.setFormatter(logging.Formatter(log_format))

            logger.addHandler(handler)

            if hasattr(cfg_preparse, 'permLog'):
                os.chmod(logfilename, cfg_preparse.permLog)

            # FIXME: https://docs.python.org/3/library/contextlib.html portable redirection...
            if sys.platform != 'win32':
                os.dup2(handler.stream.fileno(), 1)
                os.dup2(handler.stream.fileno(), 2)

        else:
            logger.setLevel(logLevel)

        signal.signal(signal.SIGTERM, self.stop_signal)
        signal.signal(signal.SIGINT, self.stop_signal)

        if cfg_preparse.statehost:
            hostdir = cfg_preparse.hostdir
        else:
            hostdir = None

        pidfilename = sarracenia.config.get_pid_filename(
            hostdir, component, config, cfg_preparse.no)
        if not os.path.isdir(os.path.dirname(pidfilename)):
            pathlib.Path(os.path.dirname(pidfilename)).mkdir(parents=True,
                                                             exist_ok=True)

        with open(pidfilename, 'w') as pfn:
            pfn.write('%d' % os.getpid())

        cfg = sarracenia.config.one_config(component, config)

        if not hasattr(cfg, 'env_declared'):
            sys.exit(0)

        for n in cfg.env_declared:
            os.environ[n] = cfg.env[n]
            os.putenv(n, cfg.env[n])

        self.running_instance = Flow.factory(cfg)

        self.running_instance.run()

        if os.path.isfile(pidfilename):
            os.unlink(pidfilename)
        sys.exit(0)


if __name__ == '__main__':
    i = instance()
    i.start()
