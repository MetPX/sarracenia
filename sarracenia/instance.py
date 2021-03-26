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
from sarracenia.moth.amqp import AMQP
import signal
import sys
import time

import appdirs
import sarracenia.config
from sarracenia.flow import Flow

from urllib.parse import urlparse, urlunparse


class RedirectedTimedRotatingFileHandler(
        logging.handlers.TimedRotatingFileHandler):
    def doRollover(self):
        super().doRollover()

        if sys.platform != 'win32':
            os.dup2(self.stream.fileno(), 1)
            os.dup2(self.stream.fileno(), 2)


class instance:
    def __init__(self):
        self.running_instance = None
        original_sigint = signal.getsignal(signal.SIGINT)

    def stop_signal(self, signum, stack):
        logging.info('signal %d received' % signum)
        self.running_instance.please_stop()

    def start(self):
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
        logging.basicConfig(
            format=
            '%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s',
            level=logging.INFO)

        # FIXME: honour SR_ variable for moving preferences...
        default_cfg_dir = appdirs.user_config_dir(
            sarracenia.config.Config.appdir_stuff['appname'],
            sarracenia.config.Config.appdir_stuff['appauthor'])

        cfg_preparse=sarracenia.config.Config( \
            {
               'accept_unmatched':False, 'exchange':None, 'inline':False, 'inline_encoding':'guess'
            } )

        defconfig = default_cfg_dir + os.sep + "default.conf"
        if os.path.exists( defconfig ):
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

        # FIXME: do we put explicit error handling here for bad input?
        #        probably worth exploring.
        #
        lr_when = cfg_preparse.lr_when
        if (type(cfg_preparse.lr_interval) == str) and (
                cfg_preparse.lr_interval[-1] in 'mMhHdD'):
            lr_when = cfg_preparse.lr_interval[-1]
            lr_interval = int(float(cfg_preparse.lr_interval[:-1]))
        else:
            lr_interval = int(float(cfg_preparse.lr_interval))

        if type(cfg_preparse.lr_backupCount) == str:
            lr_backupCount = int(float(cfg_preparse.lr_backupCount))
        else:
            lr_backupCount = cfg_preparse.lr_backupCount

        if ('audit' == cfg_preparse.configurations[0]):
            config = None
            component = 'audit'
        elif (not os.sep in cfg_preparse.configurations[0]):
            logger.critical(
                "configuration should be of the form component%sconfiguration"
                % os.sep)
            return
        else:
            component, config = cfg_preparse.configurations[0].split(os.sep)

        # init logs here. need to know instance number and configuration and component before here.
        if cfg_preparse.action == 'start':
            if cfg_preparse.statehost:
                hostdir = cfg_preparse.hostdir
            else:
                hostdir = None

            logfilename = sarracenia.config.get_log_filename(
                hostdir, component, config, cfg_preparse.no)

            #print('logfilename= %s' % logfilename )
            os.makedirs(os.path.dirname(logfilename), exist_ok=True)

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
                interval=lr_interval,
                backupCount=lr_backupCount)
            handler.setFormatter(logging.Formatter(log_format))

            logger.addHandler(handler)

            if hasattr(cfg_preparse, 'chmod_log'):
                if type(cfg_preparse.chmod) == str:
                    mode = int(cfg_preparse.chmod_log, base=8)
                else:
                    mode = cfg_preparse.chmod_log
                os.chmod(logfilename, mode)

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

        if cfg_preparse.action == 'audit':
            #FIXME: write down instance pid file. is pidfile correct for audit?
            logger.info('auditing...')
            self.running_instance = Audit()
        else:
            cfg = sarracenia.config.one_config(component, config)
            for n in cfg.env_declared:
                 os.environ[n]=cfg.env[n]
                 os.putenv(n,cfg.env[n])

            self.running_instance = Flow.factory(cfg)

        self.running_instance.run()

        if os.path.isfile(pidfilename):
            os.unlink(pidfilename)
        sys.exit(0)


if __name__ == '__main__':
    i = instance()
    i.start()
