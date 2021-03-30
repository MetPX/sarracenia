#!/usr/bin/env python3

#
# This file is part of Sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Shared Services Canada, 2019
#
"""
 Second version configuration parser

"""

import appdirs
import argparse
import copy
import inspect
import logging

import os
import pathlib
import pprint
import re
import shutil
import socket
import sys
import time
import urllib, urllib.parse

from random import randint

import sarracenia
from sarracenia import durationToSeconds, chunksize_from_str
import sarracenia.credentials
import sarracenia.flow

from sarracenia.flow.sarra import default_options as sarradefopts

import sarracenia.moth
import sarracenia.moth.amqp
import sarracenia.integrity

default_options = {
    'accept_unmatched': True,
    'baseDir': None,
    'delete': False,
    'documentRoot': None,
    'download': False,
    'inflight': None,
    'notify_only': False,
    'overwrite': True,
    'post_documentRoot': None,
    'post_baseDir': None,
    'post_baseUrl': None,
    'realpath_post': False,
    'report_back': False,
    'suppress_duplicates': 0
}

count_options = [
    'batch', 'exchange_split', 'instances', 'no', 'post_exchange_split', 'prefetch',
    'message_count_max', 'message_rate_max', 'message_rate_min'
]

# all the boolean settings.
flag_options = [ 'bind_queue', 'cache_stat', 'declare_exchange', 'debug', \
    'declare_queue', 'delete', 'discard', 'download', 'dry_run', 'durable', 'exchange_split', 'realpath_filter', \
    'follow_symlinks', 'force_polling', 'inline', 'inplace', 'log_reject', 'pipe', 'restore', \
    'report_daemons', 'mirror', 'notify_only', 'overwrite', 'post_on_start', 'poll_without_vip', \
    'preserve_mode', 'preserve_time', 'pump_flag', 'randomize', 'realpath_post', 'reconnect', \
    'report_back', 'reset', 'retry_mode', 'save', 'set_passwords', 'source_from_exchange', \
    'statehost', 'use_amqplib', 'use_pika', 'users'
                ]

duration_options = [
    'timeout', 'expire', 'housekeeping', 'message_ttl', 'retry_ttl',
    'sanity_log_dead', 'sleep', 'timeout'
]

list_options = []

size_options = ['blocksize', 'bufsize', 'bytes_per_second', 'inline_max']

str_options = [
    'admin', 'baseDir', 'broker', 'destination', 'directory', 'exchange',
    'exchange_suffix', 'events', 'feeder', 'header', 'logLevel', 'path',
    'post_baseUrl', 'post_baseDir', 'post_broker', 'post_exchange',
    'post_exchange_suffix', 'queue_name',
    'report_exchange', 'strip', 'suppress_duplicates',
    'suppress_duplicates_basis', 'tls_rigour'
]
"""
   for backward compatibility, 

   convert some old plugins that are hard to get working with
   v2wrapper, into v3 plugin.

   the fdelay ones makes in depth use of sr_replay function, and
   that has changed in v3 too much.

   accelerators and rate limiting are now built-in, no plugin required.
"""
convert_to_v3 = {
    'plugin': {
        'msg_fdelay': ['flow_callback', 'sarracenia.flowcb.filter.fdelay.FDelay'],
        'msg_pclean_f90':
        ['flow_callback', 'sarracenia.flowcb.filter.pclean_f90.PClean_F90'],
        'msg_pclean_f92':
        ['flow_callback', 'sarracenia.flowcb.filter.pclean_f92.PClean_F92'],
        'accel_wget': ['continue'],
        'accel_scp': ['continue'],
    },
    'no_download': [ 'download', 'False' ],
    'on_message': {
        'msg_delete': [
            'flow_callback',
            'sarracenia.flowcb.filter.deleteflowfiles.DeleteFlowFiles'
        ],
        'msg_rawlog': ['flow_callback', 'sarracenia.flowcb.log.Log']
    },
    'on_line': {
        'line_log': ['flow_callback', 'sarracenia.flowcb.line_log']
    },
    'before_post': {
        'post_rate_limit': ['continue']
    }
}

logger = logging.getLogger(__name__)

#    self.v2plugin_options.append(option)

#    #if not hasattr(self,option): return

#    logger.info('value type is: %s' % type(getattr(self,option)) )
#    if type(getattr(self,option)) is not list:
#        setattr(self,option, [ getattr(self,option) ] )
"""
   FIXME: respect appdir stuff using an environment variable.
   for not just hard coded as a class variable appdir_stuff

"""


def isTrue(S):
    s = S.lower()
    if s == 'true' or s == 'yes' or s == 'on' or s == '1': return True
    return False


def get_package_lib_dir():
    return os.path.dirname(inspect.getfile(Config))


def get_site_config_dir():
    return appdirs.site_config_dir(Config.appdir_stuff['appname'],
                                   Config.appdir_stuff['appauthor'])


def get_user_cache_dir(hostdir):
    """
      hostdir = None if statehost is false, 
    """
    ucd = appdirs.user_cache_dir(Config.appdir_stuff['appname'],
                                 Config.appdir_stuff['appauthor'])
    if hostdir:
        ucd = os.path.join(ucd, hostdir)
    return ucd


def get_user_config_dir():
    return appdirs.user_config_dir(Config.appdir_stuff['appname'],
                                   Config.appdir_stuff['appauthor'])


def get_pid_filename(hostdir, component, configuration, no):
    """
     return the file name for the pid file for the specified instance.
   """
    piddir = get_user_cache_dir(hostdir)
    piddir += os.sep + component + os.sep

    if configuration[-5:] == '.conf':
        configuration = configuration[:-5]

    piddir += configuration + os.sep

    return piddir + os.sep + component + '_' + configuration + '_%02d' % no + '.pid'


def get_log_filename(hostdir, component, configuration, no):
    """
      return the name of a single logfile for a single instance.
   """
    logdir = get_user_cache_dir(hostdir) + os.sep + 'log'

    if configuration is None:
        configuration = ''
    else:
        configuration = '_' + configuration

    if configuration[-5:] == '.conf':
        configuration = configuration[:-5]

    return logdir + os.sep + component + configuration + '_%02d' % no + '.log'


def wget_config(urlstr, path, remote_config_url=False):
    logger.debug("wget_config %s %s" % (urlstr, path))

    try:
        req = urllib.request.Request(urlstr)
        resp = urllib.request.urlopen(req)
        if os.path.isfile(path):
            try:
                info = resp.info()
                ts = time.strptime(info.get('Last-Modified'),
                                   "%a, %d %b %Y %H:%M:%S %Z")
                last_mod_remote = time.mktime(ts)
                last_mod_local = os.stat(path).st_mtime
                if last_mod_remote <= last_mod_local:
                    logger.info("file %s is up to date (%s)" % (path, urlstr))
                    return True
            except:
                logger.error(
                    "could not compare modification dates... downloading")
                logger.debug('Exception details: ', exc_info=True)

        fp = open(path + '.downloading', 'wb')

        # top program config only needs to keep the url
        # we set option remote_config_url with the urlstr
        # at the first line of the config...
        # includes/plugins  etc... may be left as url in the config...
        # as the urlstr is kept in the config this option would be useless
        # (and damagable for plugins)

        if remote_config_url:
            fp.write(bytes("remote_config_url %s\n" % urlstr, 'utf-8'))
        while True:
            chunk = resp.read(8192)
            if not chunk: break
            fp.write(chunk)
        fp.close()

        try:
            os.unlink(path)
        except:
            pass
        os.rename(path + '.downloading', path)

        logger.info("file %s downloaded (%s)" % (path, urlstr))

        return True

    except urllib.error.HTTPError as e:
        if os.path.isfile(path):
            logger.warning('file %s could not be processed1 (%s)' %
                           (path, urlstr))
            logger.warning('resume with the one on the server')
        else:
            logger.error('Download failed 0: %s' % urlstr)
            logger.error('Server couldn\'t fulfill the request')
            logger.error('Error code: %s, %s' % (e.code, e.reason))

    except urllib.error.URLError as e:
        if os.path.isfile(path):
            logger.warning('file %s could not be processed2 (%s)' %
                           (path, urlstr))
            logger.warning('resume with the one on the server')
        else:
            logger.error('Download failed 1: %s' % urlstr)
            logger.error('Failed to reach server. Reason: %s' % e.reason)

    except Exception as e:
        if os.path.isfile(path):
            logger.warning('file %s could not be processed3 (%s) %s' %
                           (path, urlstr, e.reason))
            logger.warning('resume with the one on the server')
        else:
            logger.error('Download failed 2: %s %s' % (urlstr, e.reason))
            logger.debug('Exception details: ', exc_info=True)

    try:
        os.unlink(path + '.downloading')
    except:
        pass

    if os.path.isfile(path):
        logger.warning("continue using existing %s" % path)

    return False


def config_path(subdir, config, mandatory=True, ctype='conf'):
    """
    Given a subdir/config look for file in configish places.

    return Tuple:   Found (True/False), path_of_file_found|config_that_was_not_found
    """
    logger.debug("config_path = %s %s" % (subdir, config))

    if config == None: return False, None

    # remote config

    if config.startswith('http:'):
        urlstr = config
        name = os.path.basename(config)
        if not name.endswith(ctype): name += '.' + ctype
        path = get_user_config_dir() + os.sep + subdir + os.sep + name
        config = name

        logger.debug("http url %s path %s name %s" % (urlstr, path, name))

        # do not allow plugin (Peter's mandatory decision)
        # because plugins may need system or python packages
        # that may not be installed on the current server.
        if subdir == 'plugins':
            logger.error("it is not allowed to download plugins")
        else:
            ok = Config.wget_config(urlstr, path)

    # priority 1 : config given is a valid path

    logger.debug("config_path %s " % config)
    if os.path.isfile(config):
        return True, config
    config_file = os.path.basename(config)
    config_name = re.sub(r'(\.inc|\.conf|\.py)', '', config_file)
    ext = config_file.replace(config_name, '')
    if ext == '': ext = '.' + ctype
    config_path = config_name + ext

    # priority 1.5: config file given without extenion...
    if os.path.isfile(config_path):
        return True, config_path

    # priority 2 : config given is a user one

    config_path = os.path.join(get_user_config_dir(), subdir,
                               config_name + ext)
    logger.debug("config_path %s " % config_path)

    if os.path.isfile(config_path):
        return True, config_path

    # priority 3 : config given to site config

    config_path = os.path.join(get_site_config_dir(), subdir,
                               config_name + ext)
    logger.debug("config_path %s " % config_path)

    if os.path.isfile(config_path):
        return True, config_path

    # priority 4 : plugins

    if subdir == 'plugins':
        config_path = get_package_lib_dir(
        ) + os.sep + 'plugins' + os.sep + config_name + ext
        logger.debug("config_path %s " % config_path)
        if os.path.isfile(config_path):
            return True, config_path

    # return bad file ...
    if mandatory:
        if subdir == 'plugins': logger.error("script not found %s" % config)
        elif config_name != 'plugins':
            logger.error("file not found %s" % config)

    return False, config


class Config:

    v2entry_points = [
        'do_download', 'do_get', 'do_poll', 'do_put', 'do_send', 'on_message',
        'on_data', 'on_file', 'on_heartbeat', 'on_housekeeping',
        'on_html_page', 'on_line', 'on_part', 'on_post', 'on_report',
        'on_start', 'on_stop', 'on_watch', 'plugin'
    ]
    components = [
        'audit', 'cpost', 'cpump', 'poll', 'post', 'sarra', 'sender', 'shovel',
        'subscribe', 'sender', 'watch', 'winnow'
    ]

    actions = [
        'add', 'cleanup', 'devsnap', 'declare', 'disable', 'dump', 'edit',
        'enable', 'foreground', 'log', 'list', 'remove', 'restart', 'sanity',
        'setup', 'show', 'start', 'stop', 'status', 'overview'
    ]

    # lookup in dictionary, respond with canonical version.
    appdir_stuff = {'appauthor': 'science.gc.ca', 'appname': 'sr3'}

    # Correct name on the right, old name on the left.
    synonyms = {
        'accel_scp_threshold': 'accel_threshold',
        'accel_wget_threshold': 'accel_threshold',
        'accept_unmatch': 'accept_unmatched',
        'basedir': 'baseDir',
        'base_dir': 'baseDir',
        'baseurl': 'baseUrl',
        'cache': 'suppress_duplicates',
        'document_root': 'documentRoot',
        'no_duplicates': 'suppress_duplicates',
        'caching': 'suppress_duplicates',
        'cache_basis': 'suppress_duplicates_basis',
        'instance': 'instances',
        'chmod': 'default_mode',
        'chmod_dir': 'default_dir_mode',
        'chmod_log': 'default_log_mode',
        'heartbeat': 'housekeeping',
        'log_format': 'logFormat',
        'll': 'logLevel',
        'loglevel': 'logLevel',
        'logdays': 'lr_backupCount',
        'logrotate_interval': 'lr_interval',
        'on_post' : 'before_post',
        'post_base_dir': 'post_baseDir',
        'post_basedir': 'post_baseDir',
        'post_base_url': 'post_baseUrl',
        'post_baseurl': 'post_baseUrl',
        'post_document_root': 'post_documentRoot',
        'post_rate_limit': 'message_rate_max',
        'post_topic_prefix' : 'post_topicPrefix',
        'topic_prefix' : 'topicPrefix'
    }
    credentials = None

    def __init__(self, parent=None):
        self.bindings = []
        self.__admin = None
        self.__broker = None
        self.__post_broker = None

        if Config.credentials is None:
            Config.credentials = sarracenia.credentials.Credentials()
            Config.credentials.read(get_user_config_dir() + os.sep +
                                    "credentials.conf")
        # FIXME... Linux only for now, no appdirs
        self.directory = None

        self.env = copy.deepcopy(os.environ)

        if parent is not None:
            for i in parent:
                setattr(self, i, parent[i])

        self.bufsize = 1024 * 1024
        self.bytes_ps = 0
        self.chmod = 0o0
        self.chmod_dir = 0o775
        self.chmod_log = 0o600

        self.debug = False
        self.declared_exchanges = []
        self.destfn_script = None
        self.env_declared = []  # list of variable that are "declared env"'d 
        self.v2plugins = {}
        self.v2plugin_options = []
        self.imports = []
        self.plugins = []
        self.exchange = None
        self.filename = None
        self.fixed_headers = {}
        self.flatten = '/'
        self.hostname = socket.getfqdn()
        self.hostdir = socket.getfqdn().split('.')[0]
        self.sleep = 0.1
        self.housekeeping = 30
        self.inline = False
        self.inline_max = 4096
        self.inline_encoding = 'guess'
        self.lr_backupCount = 5
        self.lr_interval = 1
        self.lr_when = 'midnight'
        self.masks = []
        self.instances = 1
        self.mirror = False
        self.post_exchanges = []
	#self.post_topicPrefix = None
        self.pstrip = False
        self.randid = "%04x" % randint(0, 65536)
        self.statehost = False
        self.settings = {}
        self.strip = 0
        self.timeout = 300
        self.tls_rigour = 'normal'
        self.topicPrefix = [ 'v03', 'post' ]
        self.undeclared = []
        self.declared_users = {}
        self.users = False
        self.vip = None

    def __deepcopy__(self, memo):
        """
            code for this from here: https://stackoverflow.com/questions/1500718/how-to-override-the-copy-deepcopy-operations-for-a-python-object
            Needed for python < 3.7ish? (ubuntu 18) found this bug: https://bugs.python.org/issue10076
            deepcopy fails for objects with re's in them?
            ok on ubuntu 20.04
        """
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        for k, v in self.__dict__.items():
            if k == 'masks':
                setattr(result, k, v)
            else:
                setattr(result, k, copy.deepcopy(v, memo))
        return result

    def _validate_urlstr(self, urlstr):
        # check url and add credentials if needed from credential file
        ok, details = Config.credentials.get(urlstr)
        if details is None:
            logging.error("bad credential %s" % urlstr)
            return False, urllib.parse.urlparse(urlstr)
        return True, details.url

    @property
    def admin(self):
        return self.__admin

    @admin.setter
    def admin(self, v):
        if type(v) is str:
            ok, url = self._validate_urlstr(v)
            if ok:
                self.__admin = url
        else:
            self.__admin = v

    @property
    def broker(self):
        return self.__broker

    @broker.setter
    def broker(self, v):
        if type(v) is str:
            ok, url = self._validate_urlstr(v)
            if ok:
                self.__broker = url
        else:
            self.__broker = v

    @property
    def post_broker(self):
        return self.__post_broker

    @post_broker.setter
    def post_broker(self, v):
        if type(v) is str:
            ok, url = self._validate_urlstr(v)
            if ok:
                self.__post_broker = url
        else:
            self.__post_broker = v

    def _varsub(self, word):
        """ substitute variable values from options
       """

        if word is None:
            return word
        elif type(word) in [bool, int, float]:
            return word
        elif not '$' in word:
            return word

        result = word
        if ('${BROKER_USER}' in word) and hasattr(self, 'broker') and hasattr(
                self.broker, 'username'):
            result = result.replace('${BROKER_USER}', self.broker.username)
            # FIXME: would this work also automagically if BROKER.USERNAME ?

        if not '$' in result:
            return result

        elst = []
        plst = result.split('}')
        for parts in plst:
            try:
                if '{' in parts: elst.append((parts.split('{'))[1])
            except:
                pass
        for E in elst:
            if E in ['PROGRAM']:
                e = 'program_name'
            else:
                e = E.lower()
            if hasattr(self, e):
                repval = getattr(self, e)
                if type(repval) is list:
                    repval = repval[0]
                result = result.replace('${' + E + '}', repval)
                continue

            if E in self.env.keys():
                result = result.replace('${' + E + '}', self.env[E])
                if sys.platform == 'win32':
                    result = result.replace('\\', '/')
        return result

    def _build_mask(self, option, arguments):
        """ return new entry to be appended to list of masks
       """
        regex = re.compile(arguments[0])
        if len(arguments) > 1:
            fn = arguments[1]
        else:
            fn = self.filename

        return (arguments[0], self.directory, fn, regex,
                option.lower() in ['accept', 'get'], self.mirror, self.strip,
                self.pstrip, self.flatten)

    def add_option(self, option, kind='list', default_value=None):
        """
           options can be declared in any plugin. There are various *kind* of options, where the declared type modifies the parsing.
           
           'count'      integer count type. 
           'duration'   a floating point number indicating a quantity of seconds (0.001 is 1 milisecond)
                        modified by a unit suffix ( m-minute, h-hour, w-week ) 
           'flag'       boolean (True/False) option.
           'list'       a list of string values, each succeeding occurrence catenates to the total.
                        all v2 plugin options are declared of type list.
           'size'       integer size. Suffixes k, m, and g for kilo, mega, and giga (base 2) multipliers.
           'str'        an arbitrary string value, as will all of the above types, each succeeding occurrence overrides the previous one.
    
        """
        if not hasattr(self, option):
            setattr(self, option, default_value)

        v = getattr(self, option)

        if kind == 'count':
            count_options.append(option)
            if type(v) is not int:
                setattr(self, option, int(v))
        elif kind == 'duration':
            duration_options.append(option)
            if type(v) is not float:
                setattr(self, option, durationToSeconds(v))
        elif kind == 'flag':
            flag_options.append(option)
            if type(v) is not bool:
                setattr(self, option, isTrue(v))
        elif kind == 'list':
            list_options.append(option)
            if type(v) is not list:
                setattr(self, option, [v])
        elif kind == 'size':
            size_options.append(option)
            if type(v) is not int:
                setattr(self, option, chunksize_from_str(v))

        elif kind == 'str':
            str_options.append(option)
            if type(v) is not str:
                setattr(self, option, str(v))

        logger.debug('%s declared as type:%s value:%s' % (option, type(getattr(self,option)), v))

    def dump(self):
        """ print out what the configuration looks like.
       """
        term = shutil.get_terminal_size((80, 20))
        mxcolumns = term.columns
        #logger.error('mxcolumns: %d' % mxcolumns )
        column = 0
        for k in sorted(self.__dict__.keys()):
            if k in ['env']:
                continue
            v = getattr(self, k)
            if type(v) == urllib.parse.ParseResult:
                v = v.scheme + '://' + v.username + '@' + v.hostname
            elif type(v) is str:
                v = "'%s'" % v
            ks = str(k)
            vs = str(v)

            if (not self.debug) and (len(vs) >= (mxcolumns / 2)):
                vs = '"...' + vs[-int(mxcolumns / 2):] + '"'

            last_column = column
            column += len(ks) + len(vs) + 3
            if column >= mxcolumns:
                print(',')
                column = len(ks) + len(vs) + 1
            elif last_column > 0:
                print(', ', end='')
            print(ks + '=' + vs, end='')
        print('')

    def dictify(self):
        """
      return a dict version of the cfg... 
      """
        cd = self.__dict__

        if hasattr(self, 'admin'):
            cd['admin'] = self.admin

        if hasattr(self, 'broker'):
            cd['broker'] = self.broker

        if hasattr(self, 'post_broker'):
            cd['post_broker'] = self.post_broker

        return cd

    def _merge_field(self, key, value):
        if key == 'masks':
            self.masks += value
        else:
            if value is not None:
                setattr(self, key, value)

    def merge(self, oth):
        """ 
       merge to lists of options.

       merge two lists of options if one is cumulative then merge, 
       otherwise if not None, then take value from oth
       """

        if type(oth) == dict:
            for k in oth.keys():
                self._merge_field(k, self._varsub(oth[k]))
        else:
            for k in oth.__dict__.keys():
                self._merge_field(k, self._varsub(getattr(oth, k)))

    def _override_field(self, key, value):
        if key == 'masks':
            self.masks += value
        else:
            setattr(self, key, value)

    def override(self, oth):
        """
       override a value in a set of options.

       why override() method and not just assign values to the dictionary?
       in the configuration file, there are various ways to have variable substituion.
       override invokes those, so that they are properly interpreted.  Otherwise,
       you just end up with a literal value.
       """

        if type(oth) == dict:
            for k in oth.keys():
                self._override_field(k, self._varsub(oth[k]))
        else:
            for k in oth.__dict__.keys():
                logger.error('k=%s, v=%s' % (k, getattr(oth, k)))
                self._override_field(k, self._varsub(getattr(oth, k)))

    def _resolve_exchange(self):
        if not hasattr(self, 'exchange') or self.exchange is None:
            #if hasattr(self, 'post_broker') and self.post_broker is not None:
            #    self.exchange = 'xs_%s' % self.post_broker.username
            #else:
            if self.broker.username == 'anonymous':
                self.exchange = 'xpublic'
            else:
                self.exchange = 'xs_%s' % self.broker.username

            if hasattr(self, 'exchange_suffix'):
                self.exchange += '_%s' % self.exchange_suffix

            if hasattr(self, 'exchange_split') and hasattr(
                    self, 'no') and (self.no > 0):
                self.exchange += "%02d" % self.no

    def _parse_binding(self, subtopic_string):
        """
         FIXME: see original parse, with substitions for url encoding.
                also should sqwawk about error if no exchange or topicPrefix defined.
                also None to reset to empty, not done.
       """
        self._resolve_exchange()

        if type(subtopic_string) is str:
            if not hasattr(self, 'broker'):
                logger.error( 'broker needed before subtopic' )
                return

            if self.broker.scheme == 'amq' :
                subtopic = subtopic_string.split('.')
            else:
                subtopic = subtopic_string.split('/')
            
        if hasattr(self, 'exchange') and hasattr(self, 'topicPrefix'):
            self.bindings.append((self.exchange, self.topicPrefix, subtopic))

    def _parse_v2plugin(self, entryPoint, value):
        """
       config file parsing for a v2 plugin.

       """
        if not entryPoint in Config.v2entry_points:
            logging.error(
                "undefined entry point: {} skipped".format(entryPoint))
            return

        if not entryPoint in self.v2plugins:
            self.v2plugins[entryPoint] = [value]
        else:
            self.v2plugins[entryPoint].append(value)

    def _parse_declare(self, words):

        if words[0] in ['env', 'envvar', 'var', 'value']:
            name, value = words[1].split('=')
            self.env[name] = value
            self.env_declared.append(name)
        elif words[0] in ['option', 'o']:
            self._parse_option(words[1], words[2:])
        elif words[0] in ['source', 'subscriber', 'subscribe']:
            self.declared_users[words[1]] = words[0]
        elif words[0] in ['exchange']:
            self.declared_exchanges.append(words[1])

    def _parse_setting(self, opt, value):
        """
          v3 plugin accept options for specific modules.
    
          parsed from:
          set sarracenia.flowcb.log.filter.Log.level debug

          example:   
          opt= sarracenia.flowcb.log.filter.Log.level  value = debug

          results in:
          self.settings[ sarracenia.flowcb.log.filter.Log ][level] = debug

          options should be fed to plugin class on instantiation.
          stripped of class... 
               options = { 'level' : 'debug' }
    

       """
        opt_class = '.'.join(opt.split('.')[:-1])
        opt_var = opt.split('.')[-1]
        if opt_class not in self.settings:
            self.settings[opt_class] = {}

        self.settings[opt_class][opt_var] = ' '.join(value)

    def _parse_sum(self, value):
        if (value in sarracenia.integrity.known_methods) or (
                value[0:4] == 'cod,'):
            self.sum = value
            return

        if (value[0:2] == 'z,'):
            value = value[3:]
            self.sum = 'cod,'
        else:
            self.sum = ''

        for sc in sarracenia.integrity.Integrity.__subclasses__():
            if hasattr(sc, 'registered_as') and (sc.registered_as == value):
                self.sum += sc.__name__.lower()
                return
        # FIXME this is an error return case, how to designate an invalid checksum?
        self.sum = 'invalid'

    def parse_file(self, cfg):
        """ add settings in file to self
       """
        for l in open(cfg, "r").readlines():
            line = l.split()
            if (len(line) < 1) or (line[0].startswith('#')):
                continue

            k = line[0]
            if k in Config.synonyms:
                k = Config.synonyms[k]

            if (k in convert_to_v3): 
                if (len(line) > 1):
                    v = line[1].replace('.py', '', 1)
                    if (v in convert_to_v3[k]):
                        line = convert_to_v3[k][v]
                        k = line[0]
                        logger.debug('Converting \"%s\" to v3: \"%s\"' % (l, line))
                else:
                    line = convert_to_v3[k]
                    k=line[0]
                    v=line[1] 

            if k == 'continue':
                continue

            line = list(map(lambda x: self._varsub(x), line))
            if len(line) == 1:
                v = True
            else:
                v = line[1]

            # FIXME... I think synonym check should happen here, but no time to check right now.

            if k in ['accept', 'reject', 'get']:
                self.masks.append(self._build_mask(k, line[1:]))
            elif k in [ 'callback', 'cb' ]:
                vv = v.split('.')
                v = 'sarracenia.flowcb.' + v + '.' + vv[-1].capitalize()
                self.plugins.append(v)
            elif k in [ 'callback_prepend', 'cbp' ]:
                vv = v.split('.')
                v = 'sarracenia.flowcb.' + v + '.' + vv[-1].capitalize()
                self.plugins = [ v ] + self.plugins
            elif k in ['declare']:
                self._parse_declare(line[1:])
            elif k in ['feeder']:
                self.feeder = urllib.parse.urlparse(line[1])
                self.declared_users[self.feeder.username] = 'feeder'
            elif k in ['header', 'h']:
                (kk, vv) = line[1].split('=')
                self.fixed_headers[kk] == vv
            elif k in ['include', 'config']:
                try:
                    self.parse_file(v)
                except:
                    print("failed to parse: %s" % v)
            elif k in ['subtopic']:
                self._parse_binding(v)
            elif k in ['topicPrefix']:
                if '/' in v :
                    self.topicPrefix = v.split('/')
                else:
                    self.topicPrefix = v.split('.')
            elif k in ['post_topicPrefix']:
                #if (not self.post_broker) or self.post_broker.scheme[0:3] == 'amq':
                if '/' in v :
                    self.post_topicPrefix = v.split('/')
                else:
                    self.post_topicPrefix = v.split('.')
            elif k in ['import']:
                self.imports.append(v)
            elif k in ['flow_callback', 'flowcb', 'fcb']:
                self.plugins.append(v)
            elif k in ['flow_callback_prepend', 'flowcb_prepend', 'fcbp']:
                self.plugins = [ v ] + self.plugins
            elif k in ['set', 'setting', 's']:
                self._parse_setting(line[1], line[2:])
            elif k in ['sum']:
                self._parse_sum(v)
            elif k in Config.v2entry_points:
                if k in self.plugins:
                    self.plugins.remove(v)
                self._parse_v2plugin(k, v)
            elif k in ['no-import']:
                self._parse_v3unplugin(v)
            elif k in ['inflight', 'lock']:
                if isnumeric(v[:-1]):
                    setattr(self, k, durationToSeconds(v))
                else:
                    if line[1].lower() in ['none', 'off', 'false']:
                        setattr(self, k, None)
                    else:
                        setattr(self, k, v)
            elif k in ['strip']:
                """
               2020/08/26 - PAS
               strip in config file gets translated into two separate attributes: strip and pstrip.
                 strip is the numeric variety (0-n) and if the supplied option in a regex pattern, 
                 then instead pstrip is set, and strip is set to 0.

               I don't know why it is done this way... just documenting/conforming to existing state.
               """
                if v.isdigit():
                    self.strip = int(v)
                    self.pstrip = None
                else:
                    if v[0] == '/':
                        self.pstrip = v[1:]
                    else:
                        self.pstrip = v
                    self.strip = 0
            elif k in duration_options:
                if len(line) == 1:
                    logger.error(
                        '%s is a duration option requiring a decimal number of seconds value'
                        % line[0])
                    continue
                setattr(self, k, durationToSeconds(v))
            elif k in size_options:
                if len(line) == 1:
                    logger.error(
                        '%s is a size option requiring a integer number of bytes (or multiple) value'
                        % line[0])
                    continue
                setattr(self, k, chunksize_from_str(v))
            elif k in flag_options:
                if len(line) == 1:
                    setattr(self, k, True)
                else:
                    setattr(self, k, isTrue(v))
            elif k in count_options:
                setattr(self, k, int(v))
            elif k in list_options:
                if not hasattr(self, k):
                    setattr(self, k, [' '.join(line[1:])])
                else:
                    setattr(self, k,
                            getattr(self, line[0]).append(' '.join(line[1:])))
            elif k in str_options:
                v = ' '.join(line[1:])
                setattr(self, k, v)
            else:
                #FIXME: with _options lists for all types and addition of declare, this is probably now dead code.
                #logger.info('FIXME: zombie is alive? %s' % line )
                v = ' '.join(line[1:])
                if hasattr(self, k):
                    if type(getattr(self, k)) is float:
                        setattr(self, k, float(v))
                    elif type(getattr(self, k)) is int:
                        # the only integers that have units are durations.
                        # integers without units will come out unchanged.
                        setattr(self, k, durationToSeconds(v))
                    elif type(getattr(self, k)) is str:
                        setattr(self, k, [getattr(self, k), v])
                    elif type(getattr(self, k)) is list:
                        newv=getattr(self,k)
                        newv.append(v)
                        setattr(self, k, newv)
                else:
                    # FIXME:
                    setattr(self, k, v)
                    self.undeclared.append(k)

    def fill_missing_options(self, component, config):
        """ 
         There are default options that apply only if they are not overridden... 
       """

        if hasattr(self, 'suppress_duplicates'):
            if (type(self.suppress_duplicates) is str):
                if isTrue(self.suppress_duplicates):
                    self.suppress_duplicates = 300
                else:
                    self.suppress_duplicates = durationToSeconds(
                        self.suppress_duplicates)
        else:
            self.suppress_duplicates = 0

        if self.debug:
            self.logLevel = 'debug'

        # double check to ensure duration options are properly parsed
        for d in duration_options:
            if hasattr(self, d) and (type(getattr(self, d)) is str):
                setattr(self, d, durationToSeconds(getattr(self, d)))

        if hasattr(self, 'kbytes_ps'):
            bytes_ps = chunksize_from_str(self.kbytes_ps)
            if not self.kbytes_ps[-1].isalpha():
                bytes_ps *= 1024
            setattr(self, 'bytes_per_second', bytes_ps)

        for d in count_options:
            if hasattr(self, d) and (type(getattr(self, d)) is str):
                setattr(self, d, int(getattr(self, d)))

        for d in size_options:
            if hasattr(self, d) and (type(getattr(self, d)) is str):
                setattr(self, d, chunksize_from_str(getattr(self, d)))

        for f in flag_options:
            if hasattr(self, f) and (type(getattr(self, f)) is str):
                setattr(self, f, isTrue(getattr(self, f)))

        # patch, as there is no 'none' level in python logging module...
        #    mapping so as not to break v2 configs.
        if hasattr(self, 'logLevel'):
            if self.logLevel == 'none':
                self.logLevel = 'critical'

        if not hasattr(self, 'suppress_duplicates_basis'):
            self.suppress_duplicates_basis = 'path'

        # FIXME: note that v2 *user_cache_dir* is, v3 called:  cfg_run_dir
        if config[-5:] == '.conf':
            cfg = config[:-5]
        else:
            cfg = config

        if not hasattr(self, 'post_topicPrefix'):
           self.post_topicPrefix = self.topicPrefix

        if not hasattr(self, 'cfg_run_dir'):
            if self.statehost:
                hostdir = self.hostdir
            else:
                hostdir = None
            self.cfg_run_dir = os.path.join(get_user_cache_dir(hostdir),
                                            component, cfg)
        if self.broker is not None:

            self._resolve_exchange()

            queuefile = appdirs.user_cache_dir(
                Config.appdir_stuff['appname'],
                Config.appdir_stuff['appauthor'])

            if self.statehost:
                queuefile += os.sep + self.hostdir

            queuefile += os.sep + component + os.sep + cfg
            queuefile += os.sep + component + '.' + cfg + '.' + self.broker.username

            if hasattr(self, 'exchange_split') and hasattr(
                    self, 'no') and (self.no > 0):
                queuefile += "%02d" % self.no
            queuefile += '.qname'

            self.queue_filename = queuefile

            if (not hasattr(self, 'queue_name')) or (self.queue_name is None):
                if os.path.isfile(queuefile):
                    f = open(queuefile, 'r')
                    self.queue_name = f.read()
                    f.close()
                else:
                    queue_name = 'q_' + self.broker.username + '_' + component + '.' + cfg
                    if hasattr(self, 'queue_suffix'):
                        queue_name += '.' + self.queue_suffix
                    queue_name += '.' + str(randint(0, 100000000)).zfill(8)
                    queue_name += '.' + str(randint(0, 100000000)).zfill(8)
                    self.queue_name = queue_name

            if not os.path.isdir(os.path.dirname(queuefile)):
                pathlib.Path(os.path.dirname(queuefile)).mkdir(parents=True,
                                                               exist_ok=True)

            if self.queue_name is not None:
                f = open(queuefile, 'w')
                f.write(self.queue_name)
                f.close()

        if hasattr(self, 'no'):
            if self.statehost:
                hostdir = self.hostdir
            else:
                hostdir = None
            self.pid_filename = get_pid_filename(hostdir, component, cfg,
                                                 self.no)
            self.retry_path = self.pid_filename.replace('.pid', '.retry')

        if self.post_broker is not None:
            if not hasattr(self,
                           'post_exchange') or self.post_exchange is None:
                self.post_exchange = 'xs_%s' % self.post_broker.username

            if hasattr(self, 'post_exchange_suffix'):
                self.post_exchange += '_%s' % self.post_exchange_suffix

            if hasattr(self, 'post_exchange_split'):
                l = []
                for i in range(0, int(self.post_exchange_split)):
                    y = self.post_exchange + '%02d' % i
                    l.append(y)
                self.post_exchange = l
            else:
                self.post_exchange = [self.post_exchange]

        if (self.bindings == [] and hasattr(self, 'exchange')):
            self.bindings = [(self.exchange, self.topicPrefix, [ '#' ])]

        if hasattr(self, 'documentRoot') and (self.documentRoot is not None):
            path = os.path.abspath(self.documentRoot)
            if self.realpath_post:
                path = os.path.realpath(path)

            if sys.platform == 'win32' and words0.find('\\'):
                logger.warning("%s %s" % (words0, words1))
                logger.warning(
                    "use of backslash ( \\ ) is an escape character. For a path separator use forward slash ( / )."
                )

            if sys.platform == 'win32':
                self.documentRoot = path.replace('\\', '/')
            else:
                self.documentRoot = path
            n = 2

        # verify post_baseDir

        if self.post_baseDir is None:
            if self.post_documentRoot is not None:
                self.post_baseDir = self.post_documentRoot
                logger.warning("use post_baseDir instead of post_documentRoot")
            elif self.documentRoot is not None:
                self.post_baseDir = self.documentRoot
                logger.warning("use post_baseDir instead of documentRoot")

    def check_undeclared_options(self):

        alloptions = str_options + flag_options + list_options + count_options + size_options + duration_options
        # FIXME: confused about this...  commenting out for now...
        for u in self.undeclared:
            if u not in alloptions:
                logger.error("undeclared option: %s" % u)
        logger.debug("done")

    """
      2020/05/26 FIXME here begins sheer terror.
      following routines are taken verbatim from v2. 
      trying not to touch it... it is painful.
      setting new_ values for downloading etc...
      sundew_* ... 
   """

    def sundew_basename_parts(self, pattern, basename):
        """
        modified from metpx SenderFTP
        """

        if pattern == None: return []
        parts = re.findall(pattern, basename)
        if len(parts) == 2 and parts[1] == '': parts.pop(1)
        if len(parts) != 1: return None

        lst = []
        if isinstance(parts[0], tuple):
            lst = list(parts[0])
        else:
            lst.append(parts[0])

        return lst

    # from metpx SenderFTP
    def sundew_dirPattern(self, pattern, urlstr, basename, destDir):
        """
        does substitutions for patterns in directories.

        """
        BN = basename.split(":")
        EN = BN[0].split("_")

        BP = self.sundew_basename_parts(pattern, urlstr)

        ndestDir = ""
        DD = destDir.split("/")
        for ddword in DD:
            if ddword == "": continue

            nddword = ""
            DW = ddword.split("$")
            for dwword in DW:
                nddword += self.sundew_matchPattern(BN, EN, BP, dwword, dwword)

            ndestDir += "/" + nddword

        # This code might add an unwanted '/' in front of ndestDir
        # if destDir does not start with a substitution $ and
        # if destDir does not start with a / ... it does not need one

        if (len(destDir) > 0) and (destDir[0] != '$') and (destDir[0] != '/'):
            if ndestDir[0] == '/': ndestDir = ndestDir[1:]

        return ndestDir

    def sundew_getDestInfos(self, currentFileOption, filename):
        """
        modified from sundew client

        WHATFN         -- First part (':') of filename 
        HEADFN         -- Use first 2 fields of filename
        NONE           -- Use the entire filename
        TIME or TIME:  -- TIME stamp appended
        DESTFN=fname   -- Change the filename to fname

        ex: mask[2] = 'NONE:TIME'
        """
        if currentFileOption == None: return filename
        timeSuffix = ''
        satnet = ''
        parts = filename.split(':')
        firstPart = parts[0]

        if 'sundew_extension' in msg.keys():
            parts = [parts[0]] + msg['sundew_extension'].split(':')
            filename = ':'.join(parts)

        destFileName = filename

        for spec in currentFileOption.split(':'):
            if spec == 'WHATFN':
                destFileName = firstPart
            elif spec == 'HEADFN':
                headParts = firstPart.split('_')
                if len(headParts) >= 2:
                    destFileName = headParts[0] + '_' + headParts[1]
                else:
                    destFileName = headParts[0]
            elif spec == 'SENDER' and 'SENDER=' in filename:
                i = filename.find('SENDER=')
                if i >= 0: destFileName = filename[i + 7:].split(':')[0]
                if destFileName[-1] == ':': destFileName = destFileName[:-1]
            elif spec == 'NONE':
                if 'SENDER=' in filename:
                    i = filename.find('SENDER=')
                    destFileName = filename[:i]
                else:
                    if len(parts) >= 6:
                        # PX default behavior : keep 6 first fields
                        destFileName = ':'.join(parts[:6])
                        #  PDS default behavior  keep 5 first fields
                        if len(parts[4]) != 1:
                            destFileName = ':'.join(parts[:5])
                # extra trailing : removed if present
                if destFileName[-1] == ':': destFileName = destFileName[:-1]
            elif spec == 'NONESENDER':
                if 'SENDER=' in filename:
                    i = filename.find('SENDER=')
                    j = filename.find(':', i)
                    destFileName = filename[:i + j]
                else:
                    if len(parts) >= 6:
                        # PX default behavior : keep 6 first fields
                        destFileName = ':'.join(parts[:6])
                        #  PDS default behavior  keep 5 first fields
                        if len(parts[4]) != 1:
                            destFileName = ':'.join(parts[:5])
                # extra trailing : removed if present
                if destFileName[-1] == ':': destFileName = destFileName[:-1]
            elif re.compile('SATNET=.*').match(spec):
                satnet = ':' + spec
            elif re.compile('DESTFN=.*').match(spec):
                destFileName = spec[7:]
            elif re.compile('DESTFNSCRIPT=.*').match(spec):
                old_destfn_script = self.destfn_script
                saved_new_file = msg['new_file']
                msg['new_file'] = destFileName
                self.destfn_script = None
                script = spec[13:]
                self.execfile('destfn_script', script)
                if self.destfn_script != None:
                    ok = self.destfn_script(self)
                destFileName = msg['new_file']
                self.destfn_script = old_destfn_script
                msg['new_file'] = saved_new_file
                if destFileName == None: destFileName = old_destFileName
            elif spec == 'TIME':
                timeSuffix = ':' + time.strftime("%Y%m%d%H%M%S", time.gmtime())
                if 'pubTime' in msg:
                    timeSuffix = ":" + msg['pubTime'].split('.')[0]
                if 'pubTime' in msg:
                    timeSuffix = ":" + msg['pubtime'].split('.')[0]
                    timeSuffix = timeSuffix.replace('T', '')
                # check for PX or PDS behavior ...
                # if file already had a time extension keep his...
                if len(parts[-1]) == 14 and parts[-1][0] == '2':
                    timeSuffix = ':' + parts[-1]

            else:
                logger.error("Don't understand this DESTFN parameter: %s" %
                             spec)
                return (None, None)
        return destFileName + satnet + timeSuffix

    # modified from metpx SenderFTP
    def sundew_matchPattern(self, BN, EN, BP, keywd, defval):

        BN6 = time.strftime("%Y%m%d%H%M%S", time.gmtime())
        if len(BN) >= 7: BN6 = BN[6]

        if keywd[:4] == "{T1}": return (EN[0])[0:1] + keywd[4:]
        elif keywd[:4] == "{T2}": return (EN[0])[1:2] + keywd[4:]
        elif keywd[:4] == "{A1}": return (EN[0])[2:3] + keywd[4:]
        elif keywd[:4] == "{A2}": return (EN[0])[3:4] + keywd[4:]
        elif keywd[:4] == "{ii}": return (EN[0])[4:6] + keywd[4:]
        elif keywd[:6] == "{CCCC}": return EN[1] + keywd[6:]
        elif keywd[:4] == "{YY}": return (EN[2])[0:2] + keywd[4:]
        elif keywd[:4] == "{GG}": return (EN[2])[2:4] + keywd[4:]
        elif keywd[:4] == "{Gg}": return (EN[2])[4:6] + keywd[4:]
        elif keywd[:5] == "{BBB}":
            return (EN[3])[0:3] + keywd[5:]
            # from pds'datetime suffix... not sure
        elif keywd[:7] == "{RYYYY}":
            return BN6[0:4] + keywd[7:]
        elif keywd[:5] == "{RMM}":
            return BN6[4:6] + keywd[5:]
        elif keywd[:5] == "{RDD}":
            return BN6[6:8] + keywd[5:]
        elif keywd[:5] == "{RHH}":
            return BN6[8:10] + keywd[5:]
        elif keywd[:5] == "{RMN}":
            return BN6[10:12] + keywd[5:]
        elif keywd[:5] == "{RSS}":
            return BN6[12:14] + keywd[5:]

        # Matching with basename parts if given

        if BP != None:
            for i, v in enumerate(BP):
                kw = '{' + str(i) + '}'
                lkw = len(kw)
                if keywd[:lkw] == kw: return v + keywd[lkw:]

        return defval

    def set_dir_pattern(self, cdir):

        if not '$' in cdir:
            return cdir

        new_dir = cdir

        if '${BD}' in cdir and self.baseDir != None:
            new_dir = new_dir.replace('${BD}', self.baseDir)

        if '${PBD}' in cdir and self.post_baseDir != None:
            new_dir = new_dir.replace('${PBD}', self.post_baseDir)

        if '${DR}' in cdir and self.documentRoot != None:
            logger.warning(
                "DR = documentRoot should be replaced by BD for base_dir")
            new_dir = new_dir.replace('${DR}', self.documentRoot)

        if '${PDR}' in cdir and self.post_baseDir != None:
            logger.warning(
                "PDR = post_documentRoot should be replaced by PBD for post_baseDir"
            )
            new_dir = new_dir.replace('${PDR}', self.post_baseDir)

        if '${YYYYMMDD}' in cdir:
            YYYYMMDD = time.strftime("%Y%m%d", time.gmtime())
            new_dir = new_dir.replace('${YYYYMMDD}', YYYYMMDD)

        if '${SOURCE}' in cdir:
            new_dir = new_dir.replace('${SOURCE}', msg['source'])

        if '${DD}' in cdir:
            DD = time.strftime("%d", time.gmtime())
            new_dir = new_dir.replace('${DD}', DD)

        if '${HH}' in cdir:
            HH = time.strftime("%H", time.gmtime())
            new_dir = new_dir.replace('${HH}', HH)

        if '${YYYY}' in cdir:
            YYYY = time.strftime("%Y", time.gmtime())
            new_dir = new_dir.replace('${YYYY}', YYYY)

        if '${MM}' in cdir:
            MM = time.strftime("%m", time.gmtime())
            new_dir = new_dir.replace('${MM}', MM)

        if '${JJJ}' in cdir:
            JJJ = time.strftime("%j", time.gmtime())
            new_dir = new_dir.replace('${JJJ}', JJJ)

        # Parsing cdir to subtract time from it in the following formats
        # time unit can be: sec/mins/hours/days/weeks

        # ${YYYY-[number][time_unit]}
        offset_check = re.search(r'\$\{YYYY-(\d+)(\D)\}', cdir)
        if offset_check:
            seconds = self.duration_from_str(''.join(offset_check.group(1, 2)),
                                             's')

            epoch = time.mktime(time.gmtime()) - seconds
            YYYY1D = time.strftime("%Y", time.localtime(epoch))
            new_dir = re.sub('\$\{YYYY-\d+\D\}', YYYY1D, new_dir)

        # ${MM-[number][time_unit]}
        offset_check = re.search(r'\$\{MM-(\d+)(\D)\}', cdir)
        if offset_check:
            seconds = self.duration_from_str(''.join(offset_check.group(1, 2)),
                                             's')

            epoch = time.mktime(time.gmtime()) - seconds
            MM1D = time.strftime("%m", time.localtime(epoch))
            new_dir = re.sub('\$\{MM-\d+\D\}', MM1D, new_dir)

        # ${JJJ-[number][time_unit]}
        offset_check = re.search(r'\$\{JJJ-(\d+)(\D)\}', cdir)
        if offset_check:
            seconds = self.duration_from_str(''.join(offset_check.group(1, 2)),
                                             's')

            epoch = time.mktime(time.gmtime()) - seconds
            JJJ1D = time.strftime("%j", time.localtime(epoch))
            new_dir = re.sub('\$\{JJJ-\d+\D\}', JJJ1D, new_dir)

        # ${YYYYMMDD-[number][time_unit]}
        offset_check = re.search(r'\$\{YYYYMMDD-(\d+)(\D)\}', cdir)
        if offset_check:
            seconds = self.duration_from_str(''.join(offset_check.group(1, 2)),
                                             's')

            epoch = time.mktime(time.gmtime()) - seconds
            YYYYMMDD = time.strftime("%Y%m%d", time.localtime(epoch))
            new_dir = re.sub('\$\{YYYYMMDD-\d+\D\}', YYYYMMDD, new_dir)

        new_dir = self._varsub(new_dir)

        return new_dir

    # ==============================================
    # how will the download file land on this server
    # with all options, this is really tricky
    # ==============================================

    def set_newMessageFields(self, msg, urlstr, pattern, maskDir,
                             maskFileOption, mirror, strip, pstrip, flatten):

        msg['_deleteOnPost'] |= set( ['new_dir', 'new_file', 'new_relPath', 'new_baseUrl'] )

        # relative path by default mirror

        relPath = '%s' % msg['relPath']

        # case S=0  sr_post -> sr_suscribe... rename in headers
        # FIXME: 255 char limit on headers, rename will break!
        if 'rename' in msg: relPath = '%s' % msg['rename']

        token = relPath.split('/')
        filename = token[-1]

        # if provided, strip (integer) ... strip N heading directories
        #         or  pstrip (pattern str) strip regexp pattern from relPath
        # cannot have both (see setting of option strip in sr_config)

        if strip > 0:
            #MG folling code was a fix...
            #   if strip is a number of directories
            #   add 1 to strip not to count '/'
            #   impact to current configs avoided by commenting out

            #if relPath[0] == '/' : strip = strip + 1
            try:
                token = token[strip:]

            # strip too much... keep the filename
            except:
                token = [filename]

        # strip using a pattern

        elif pstrip != None:

            #MG FIXME Peter's wish to have replacement in pstrip (ex.:${SOURCE}...)
            try:
                relstrip = re.sub(pstrip, '', relPath, 1)
            except:
                relstrip = relPath

            # if filename dissappear... same as numeric strip, keep the filename
            if not filename in relstrip: relstrip = filename
            token = relstrip.split('/')

        # if flatten... we flatten relative path
        # strip taken into account

        if flatten != '/':
            filename = flatten.join(token)
            token[-1] = [filename]

        if maskFileOption != None:
            try:
                filename = self.sundew_getDestInfos(filename)
            except:
                logger.error("problem with accept file option %s" %
                             maskFileOption)
            token[-1] = [filename]

        # MG this was taken from the sr_sender when not derived from sr_subscribe.
        # if a desftn_script is set in a plugin, it is going to be applied on all file
        # this might be confusing

        if self.destfn_script:
            self.new_file = filename
            ok = self.destfn_script(self)
            if filename != self.new_file:
                logger.debug("destfn_script : %s becomes %s " %
                             (filename, self.new_file))
                filename = self.new_file
                token[-1] = [filename]

        # not mirroring

        if not mirror:
            token = [filename]

        # uses current dir

        #if self.currentDir : new_dir = self.currentDir
        if maskDir:
            new_dir = maskDir
        else:
            new_dir = ''

        if self.baseDir:
            if new_dir :
                d=new_dir
            elif self.post_baseDir:
                d=self.post_baseDir
            else:
                d=None

            if d:
                for f in [ 'link', 'oldname', 'newname' ]:
                    if f in msg:
                        msg[f] = msg[f].replace( self.baseDir, d )

        # add relPath

        if len(token) > 1:
            new_dir = new_dir + '/' + '/'.join(token[:-1])

        new_dir = self.set_dir_pattern(new_dir)

        # resolution of sundew's dirPattern

        tfname = filename
        if 'sundew_extension' in msg.keys():
            tfname = filename.split(':')[0] + ':' + msg['sundew_extension']

        # when sr_sender did not derived from sr_subscribe it was always called
        new_dir = self.sundew_dirPattern(pattern, urlstr, tfname, new_dir)

        # reset relPath from new_dir

        # FIXME: 2020/09/05 - PAS ... normpath will put back slashes in on Windows.
        # normpath thing is probably wrong... not sure why it is here...
        if 'new_dir' not in msg:
            #msg['new_dir'] = os.path.normpath(new_dir)
            msg['new_dir'] = new_dir

        relPath = msg['new_dir'] + '/' + filename

        if self.post_baseDir:
            relPath = relPath.replace(self.set_dir_pattern(self.post_baseDir), '')

        if relPath[0] == '/':
            relPath = relPath[1:]

        # set the results for the new file (downloading or sending)

        # final value
        # NOTE : normpath keeps '/a/b/c' and '//a/b/c' the same
        #        Everywhere else // or /../ are corrected.
        #        but if the number of / starting the path > 2  ... it will result into 1 /

        #msg['new_relPath'] = os.path.normpath(relPath)
        msg['new_relPath'] = relPath

        if sys.platform == 'win32':
            if 'new_dir' not in msg:
                msg['new_dir'] = msg['new_dir'].replace('\\', '/')
            msg['new_relPath'] = msg['new_relPath'].replace('\\', '/')
            if re.match('[A-Z]:', str(self.currentDir), flags=re.IGNORECASE):
                msg['new_dir'] = msg['new_dir'].lstrip('/')
                msg['new_relPath'] = msg['new_relPath'].lstrip('/')

        msg['new_file'] = filename

        if self.post_broker and self.post_baseUrl:
            msg['new_baseUrl'] = self.set_dir_pattern( self.post_baseUrl )
        else:
            msg['new_baseUrl'] = msg['baseUrl']

        if 'new_relPath' in msg:
            offset = 1 if msg['new_relPath'][0] == '/' else 0
            msg['subtopic'] = msg['new_relPath'].split('/')[offset:-1]

        #logger.debug( "leaving with: new_dir=%s new_relpath=%s new_baseUrl=%s " % \
        #   ( msg['new_dir'], msg['new_relPath'], msg['new_baseUrl'] ) )

    """
       2020/05/26 PAS... FIXME: end of sheer terror. 
   """

    class addBinding(argparse.Action):
        """
        called by argparse to deal with queue bindings.
        """
        def __call__(self, parser, namespace, values, option_string):

            if values == 'None':
                namespace.bindings = []

            namespace._resolve_exchange()

            if not hasattr(namespace, 'broker'):
                raise 'broker needed before subtopic'
                return

            if not hasattr(namespace, 'exchange'):
                raise 'exchange needed before subtopic'
                return

            if not hasattr(namespace, 'topicPrefix'):
                raise 'topicPrefix needed before subtopic'
                return

            if type(namespace.topicPrefix) is str:
               if namespace.broker.scheme[0:3] == 'amq':
                   topicPrefix = namespace.topicPrefix.split('.')
               else:
                   topicPrefix = namespace.topicPrefix.split('/')

            namespace.bindings.append(
                (namespace.exchange, topicPrefix, values))

    def parse_args(self, isPost=False):
        """
        user information:
           accept a configguration, apply argParse library to augment the given configuration
           with command line settings.

           the post component has a different calling convention than others, so use that flag
           if called from post.

        development notes:
           Use argparse.parser to modify defaults.
           FIXME, many FIXME notes below. this is a currently unusable placeholder.
           have not figured this out yet. many issues.

           FIXME #1:
           parseArgs often sets the value of the variable, regardless of it's presence (normally a good thing.)
           ( if you have 'store_true' then default needed, for broker, just a string, it ignores if not present.)
           This has the effect of overriding settings in the file parsed before the arguments.
           Therefore: often supply defaults... but... sigh...
           
           but there is another consideration stopping me from supplying defaults, wish I remembered what it was.
           I think it is:
           FIXME #2: 
           arguments are parsed twice: once to get basic stuff (loglevel, component, action)
           and if the parsing fails there, the usage will print the wrong defaults... 

        """

        parser=argparse.ArgumentParser( \
             description='version: %s\nSarracenia flexible tree copy entry point' % sarracenia.__version__ ,\
             formatter_class=argparse.ArgumentDefaultsHelpFormatter )

        parser.add_argument('--accept_unmatched',
                            default=self.accept_unmatched,
                            type=bool,
                            nargs='?',
                            help='default selection, if nothing matches')
        parser.add_argument(
            '--action',
            '-a',
            nargs='?',
            choices=Config.actions,
            help='action to take on the specified configurations')
        parser.add_argument('--admin',
                            help='amqp://user@host of peer to manage')
        parser.add_argument(
            '--attempts',
            type=int,
            nargs='?',
            help='how many times to try before queuing for retry')
        parser.add_argument(
            '--base_dir',
            '-bd',
            nargs='?',
            help="path to root of tree for relPaths in messages.")
        parser.add_argument('--batch',
                            type=int,
                            nargs='?',
                            help='how many transfers per each connection')
        parser.add_argument(
            '--blocksize',
            type=int,
            nargs='?',
            help=
            'size to partition files. 0-guess, 1-never, any other number: that size'
        )
        """
           FIXME:  Most of this is gobblygook place holder stuff, by copying from wmo-mesh example.
           Don't really need this to work right now, so just leaving it around as-is.  Challenges:

           -- sizing units,  K, M, G, 
           -- time units s,h,m,d
           -- what to do with verbos.
           -- accept/reject whole mess requires extension deriving a class from argparse.Action.
           
        """
        parser.add_argument('--broker',
                            nargs='?',
                            help='amqp://user:pw@host of peer to subscribe to')
        parser.add_argument('--config',
                            '-c',
                            nargs='?',
                            help=' specifical configuration to select ')
        parser.add_argument('--dangerWillRobinson',
                            action='store_true',
                            default=False,
                            help='Confirm you want to do something dangerous')
        parser.add_argument('--debug',
                            action='store_true',
                            default=self.debug,
                            help='pring debugging output (very verbose)')
        parser.add_argument('--exchange',
                            nargs='?',
                            default=self.exchange,
                            help='root of the topic tree to subscribe to')
        """
        FIXME: header option not implemented in argparsing: should add to the fixed_header dictionary.
          
        """
        """
        FIXME: in previous parser, exchange is a modifier for bindings, can have several different values for different subtopic bindings.
           as currently coded, just a single value that over-writes previous setting, so only binding to a single exchange is possible.
        """

        parser.add_argument('--inline',
                            dest='inline',
                            default=self.inline,
                            action='store_true',
                            help='include file data in the message')
        parser.add_argument(
            '--inline_encoding',
            choices=['text', 'binary', 'guess'],
            default=self.inline_encoding,
            help='encode payload in base64 (for binary) or text (utf-8)')
        parser.add_argument('--inline_max',
                            type=int,
                            default=self.inline_max,
                            help='maximum message size to inline')
        parser.add_argument(
            '--instances',
            type=int,
            help='number of processes to run per configuration')

        parser.set_defaults(bindings=[])

        parser.add_argument(
            '--logLevel',
            choices=[
                'notset', 'debug', 'info', 'warning', 'error', 'critical'
            ],
            help='encode payload in base64 (for binary) or text (utf-8)')
        parser.add_argument('--no',
                            type=int,
                            help='instance number of this process')
        parser.add_argument('--queue_name',
                            nargs='?',
                            help='name of AMQP consumer queue to create')
        parser.add_argument('--post_broker',
                            nargs='?',
                            help='broker to post downloaded files to')
        #parser.add_argument('--post_baseUrl', help='base url of the files announced')
        parser.add_argument('--post_exchange',
                            nargs='?',
                            help='root of the topic tree to announce')
        parser.add_argument(
            '--post_exchange_split',
            type=int,
            nargs='?',
            help='split output into different exchanges 00,01,...')
        parser.add_argument(
            '--post_topicPrefix',
            nargs='?',
            help=
            'allows simultaneous use of multiple versions and types of messages'
        )
        parser.add_argument(
            '--topicPrefix',
            nargs='?',
            default=self.topicPrefix,
            help=
            'allows simultaneous use of multiple versions and types of messages'
        )
        #FIXME: select/accept/reject in parser not implemented.
        parser.add_argument(
            '--select',
            nargs=1,
            action='append',
            help='client-side filtering: accept/reject <regexp>')
        parser.add_argument(
            '--subtopic',
            nargs=1,
            action=Config.addBinding,
            help=
            'server-side filtering: MQTT subtopic, wilcards # to match rest, + to match one topic'
        )
        parser.add_argument('--users',
                            default=False,
                            action='store_true',
                            help='only for declare... declare users?')
        parser.add_argument(
            '--version',
            '-v',
            action='version',
            version='%s' % sarracenia.__version__,
            help=
            'server-side filtering: MQTT subtopic, wilcards # to match rest, + to match one topic'
        )

        if isPost:
            parser.add_argument('--path',
                                '-p',
                                action='append',
                                nargs='?',
                                help='path to post or watch')
            parser.add_argument('path',
                                nargs='*',
                                action='extend',
                                help='files to post')
        else:
            parser.add_argument(
                'action',
                nargs='?',
                choices=Config.actions,
                help='action to take on the specified configurations')
            parser.add_argument('configurations',
                                nargs='*',
                                help='configurations to operate on')

        args = parser.parse_args()

        if hasattr(args, 'help'):
            args.print_usage()

        if hasattr(args, 'config') and (args.config is not None):
            args.configurations = [args.config]

        #FIXME need to apply _varsub

        self.merge(args)


def default_config():

    cfg = Config()
    cfg.currentDir = None
    cfg.override(default_options)
    cfg.override(sarracenia.moth.default_options)
    cfg.override(sarracenia.moth.amqp.default_options)
    cfg.override(sarracenia.flow.default_options)

    for g in ["admin.conf", "default.conf"]:
        if os.path.exists(get_user_config_dir() + os.sep + g):
            cfg.parse_file(get_user_config_dir() + os.sep + g)

    return cfg

def no_file_config():
    """
      initialize a config that will not use Sarracenia configuration files at all.
      meant for use by people writing independent programs to start up instances
      with python API calls.

    """
    cfg = Config()
    cfg.currentDir = None
    cfg.override(default_options)
    cfg.override(sarracenia.moth.default_options)
    cfg.override(sarracenia.moth.amqp.default_options)
    cfg.override(sarracenia.flow.default_options)
    cfg.cfg_run_dir = '.'
    cfg.retry_path = '.'
    return cfg

def one_config(component, config, isPost=False):
    """
      single call return a fully parsed single configuration for a single component to run.

      read in admin.conf and default.conf

      apply component default overrides ( maps to: component/check ?)
      read in component/config.conf
      parse arguments from command line.
      return config instance item.

      
      appdir_stuff can be to override file locations for testing during development.

    """
    default_cfg = default_config()
    #default_cfg.override(  { 'program_name':component, 'directory': os.getcwd(), 'accept_unmatched':True, 'no':0 } )
    default_cfg.override({
        'program_name': component,
        'accept_unmatched': True,
        'no': 0
    })

    #logger.error( 'default' )
    #print( 'default' )
    #default_cfg.dump()

    cfg = copy.deepcopy(default_cfg)

    if component in ['post']:
        cfg.override(sarracenia.flow.post.default_options)
    elif component in ['poll']:
        cfg.override(sarracenia.flow.poll.default_options)
    elif component in ['sarra']:
        cfg.override(sarradefopts)
    elif component in ['sender']:
        cfg.override(sarracenia.flow.sender.default_options)
    elif component in ['subscribe']:
        cfg.override(sarracenia.flow.subscribe.default_options)
    elif component in ['watch']:
        cfg.override(sarracenia.flow.watch.default_options)

    store_pwd = os.getcwd()

    os.chdir(get_user_config_dir())
    os.chdir(component)

    if config[-5:] != '.conf':
        fname = config + '.conf'
    else:
        fname = config

    if os.path.exists(fname):
         cfg.parse_file(fname)
    else:
         logger.error('config %s not found' % fname )
         return None

    #logger.error( 'after file' )
    #print( 'after file' )
    #cfg.dump()
    os.chdir(store_pwd)

    cfg.parse_args(isPost)

    #logger.error( 'after args' )
    #print( 'after args' )
    #cfg.dump()

    cfg.fill_missing_options(component, config)

    if component in ['post', 'watch']:
        cfg.postpath = cfg.configurations[1:]
        if hasattr(cfg, 'path') and (cfg is not None):
            if type(cfg.path) is list:
                cfg.postpath.extend(cfg.path)
            else:
                cfg.postpath.append(cfg.path)
            logger.debug('path is : %s' % cfg.path)
            logger.debug('postpath is : %s' % cfg.postpath)
    #pp = pprint.PrettyPrinter(depth=6)
    #pp.pprint(cfg)

    return cfg


# add directory to python front of search path for plugins.

plugin_dir = get_user_config_dir() + os.sep + "plugins"
if os.path.isdir(plugin_dir) and not plugin_dir in sys.path:
    sys.path.insert(0, plugin_dir)
