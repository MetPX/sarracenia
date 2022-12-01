# This file is part of Sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Shared Services Canada, 2019
#
"""
 Second version configuration parser

"""

import argparse
import copy
import humanfriendly
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

if sys.version_info[0] >= 3 and sys.version_info[1] < 8:
    """
        'extend' action not included in argparse prior to python 3.8
        https://stackoverflow.com/questions/41152799/argparse-flatten-the-result-of-action-append
    """
 
    class ExtendAction(argparse.Action):

        def __call__(self, parser, namespace, values, option_string=None):
            items = getattr(namespace, self.dest) or []
            items.extend(values)
            setattr(namespace, self.dest, items)




import sarracenia
from sarracenia import durationToSeconds, site_config_dir, user_config_dir, user_cache_dir
import sarracenia.credentials
import sarracenia.flow
import sarracenia.flowcb

from sarracenia.flow.sarra import default_options as sarradefopts

import sarracenia.integrity.arbitrary

import sarracenia.moth
import sarracenia.integrity
import sarracenia.instance

default_options = {
    'acceptSizeWrong': False,
    'acceptUnmatched': True,
    'baseDir': None,
    'baseUrl_relPath': False,
    'delete': False,
    'documentRoot': None,
    'download': False,
    'filename': 'WHATFN',
    'flowMain': None,
    'inflight': None,
    'inline': False,
    'inlineOnly': False,
    'integrity_method': 'sha512',
    'logStdout': False,
    'nodupe_ttl': 0,
    'overwrite': True,
    'path': [],
    'permDefault': 0,
    'permDirDefault': 0o775,
    'permLog': 0o600,
    'please_stop_immediately': False,
    'post_documentRoot': None,
    'post_baseDir': None,
    'post_baseUrl': None,
    'realpath_post': False,
    'report': False,
    'retryEmptyBeforeExit': False,
    'sourceFromExchange': False,
    'v2compatRenameDoublePost': False,
    'varTimeOffset': 0
}

count_options = [
    'batch', 'exchangeSplit', 'instances', 'no', 'post_exchangeSplit', 'prefetch',
    'messageCountMax', 'messageRateMax', 'messageRateMin'
]

# all the boolean settings.
flag_options = [ 'acceptSizeWrong', 'acceptUnmatched', 'baseUrl_relPath', 'cache_stat', 'debug', \
    'delete', 'discard', 'download', 'dry_run', 'durable', 'exchangeDeclare', 'exchangeSplit', 'logReject', 'realpath_filter', \
    'follow_symlinks', 'force_polling', 'inline', 'inlineOnly', 'inplace', 'logStdout', 'logReject', 'restore', \
    'messageDebugDump', 'mirror', 'timeCopy', 'notify_only', 'overwrite', 'please_stop_immediately', 'post_on_start', \
    'permCopy', 'pump_flag', 'queueBind', 'queueDeclare', 'randomize', 'realpath_post', 'reconnect', \
    'report', 'reset', 'retry_mode', 'retryEmptyBeforeExit', 'save', 'set_passwords', 'sourceFromExchange', \
    'statehost', 'users', 'v2compatRenameDoublePost'
                ]

float_options = [ ]

duration_options = [
    'expire', 'housekeeping', 'message_ttl', 'nodupe_fileAgeMax', 'retry_ttl',
    'sanity_log_dead', 'sleep', 'timeout', 'varTimeOffset'
]

list_options = ['path']

# set, valid values of the set.
set_options = [ 'logEvents', 'fileEvents' ]

set_choices = { 
    'logEvents': sarracenia.flowcb.entry_points + [ 'reject', 'all' ],
    'fileEvents': set( [ 'create', 'delete', 'link', 'modify' ] )
 }
# FIXME: doesn't work... wonder why?
#    'fileEvents': sarracenia.flow.allFileEvents
 
perm_options = [ 'permDefault', 'permDirDefault','permLog']

size_options = ['accelThreshold', 'blocksize', 'bufsize', 'byteRateMax', 'inlineByteMax']

str_options = [
    'admin', 'baseDir', 'broker', 'cluster', 'directory', 'exchange',
    'exchange_suffix', 'feeder', 'filename', 'flowMain', 'header', 'integrity', 'logLevel', 
    'pollUrl', 'post_baseUrl', 'post_baseDir', 'post_broker', 'post_exchange',
    'post_exchangeSuffix', 'queueName', 'remoteUrl',
    'report_exchange', 'source', 'strip', 'timezone', 'nodupe_ttl',
    'nodupe_basis', 'tlsRigour', 'vip'
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
    'ls_file_index' : [ 'continue' ],
    'plugin': {
        'msg_fdelay': ['callback', 'filter.fdelay'],
        'msg_pclean_f90':
        ['callback', 'filter.pclean_f90.PClean_F90'],
        'msg_pclean_f92':
        ['callback', 'filter.pclean_f92.PClean_F92'],
        'accel_wget': ['continue'],
        'accel_scp': ['continue'],
        'accel_cp': ['continue'],
        'msg_total_save': ['continue'],
        'post_total_save': ['continue'],
        'post_total_interval': ['continue']
    },
    'do_send': {
       'file_email' : [ 'callback', 'send.email' ],
    },
    'no_download': [ 'download', 'False' ],
    'notify_only': [ 'download', 'False' ],
    'on_file': {
        'file_age' : [ 'callback', 'work.age' ],
    },
    'on_message': {
        'msg_print_lag': [ 'callback', 'accept.printlag.PrintLag'],
        'msg_replace_new_dir': [ 'callback', 'accept.pathreplace' ],
        'msg_skip_old': [ 'callback', 'accept.skipold.SkipOld'],
        'msg_test_retry': [ 'callback', 'accept.testretry.TestRetry'],
        'msg_to_clusters': [ 'callback', 'accept.toclusters.ToClusters'],
        'msg_save': [ 'callback', 'accept.save'],
        'msg_2localfile': [ 'callback', 'accept.tolocalfile.ToLocalFile'],
        'msg_rename_whatfn': [ 'callback', 'accept.renamewhatfn.RenameWhatFn'],
        'msg_rename_dmf': [ 'callback', 'accept.renamedmf.RenameDMF'],
        'msg_hour_tree': [ 'callback', 'accept.hourtree.HourTree'],
        'msg_renamer': [ 'callback', 'accept.renamer.Renamer'],
        'msg_2http': [ 'callback', 'accept.tohttp.ToHttp'],
        'msg_2local': [ 'callback', 'accept.tolocal.ToLocal'],
        'msg_http_to_https': [ 'callback', 'accept.httptohttps.HttpToHttps'],
        'msg_speedo': [ 'callback', 'accept.speedo.Speedo'],
        'msg_WMO_type_suffix': [ 'callback', 'accept.wmotypesuffix.WmoTypeSuffix'],
        'msg_sundew_pxroute': [ 'callback', 'accept.sundewpxroute.SundewPxRoute'],
        'msg_rename4jicc': [ 'flow_callback', 'accept.rename4jicc.Rename4Jicc'],
        'msg_delay': [ 'callback', 'accept.messagedelay.MessageDelay'],
        'msg_download_baseurl': [ 'callback', 'accept.downloadbaseurl.DownloadBaseUrl'],
	'msg_from_cluster': ['continue'],
	'msg_stdfiles': ['continue'],
	'msg_fdelay': ['callback', 'filter.fdelay'],
	'msg_stopper': ['continue'],
	'msg_overwrite_sum': ['continue'],
	'msg_gts2wistopic': ['continue'],
	'msg_download': ['continue'],
	'msg_by_source': ['continue'],
	'msg_by_user': ['continue'],
	'msg_dump': ['continue'],
	'msg_total': ['continue'],
	'post_total': ['continue'],
        'wmo2msc': [ 'callback', 'filter.wmo2msc.Wmo2Msc'],
        'msg_delete': [ 'callback', 'filter.deleteflowfiles.DeleteFlowFiles'],
        'msg_log': ['logEvents', 'after_accept'],
        'msg_rawlog': ['logEvents', 'after_accept'],
        'post_hour_tree': [ 'callback', 'accept.posthourtree.PostHourTree'],
        'post_long_flow': [ 'callback', 'accept.longflow.LongFLow'],
        'post_override': [ 'callback', 'accept.postoverride.PostOverride'],
	'post_rate_limit': ['continue'],
        'to': ['continue']
    },
    'on_post': {
        'post_log': ['logEvents', 'after_work']
    },
    'recursive' : ['continue'],
    'report_daemons': ['continue'],
    'windows_run': [ 'continue' ],
    'xattr_disable': [ 'continue' ]
}

logger = logging.getLogger(__name__)

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
    return sarracenia.site_config_dir(Config.appdir_stuff['appname'],
                                   Config.appdir_stuff['appauthor'])


def get_user_cache_dir(hostdir):
    """
      hostdir = None if statehost is false, 
    """
    ucd = sarracenia.user_cache_dir(Config.appdir_stuff['appname'],
                                 Config.appdir_stuff['appauthor'])
    if hostdir:
        ucd = os.path.join(ucd, hostdir)
    return ucd


def get_user_config_dir():
    return sarracenia.user_config_dir(Config.appdir_stuff['appname'],
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
    """
       The option parser to produce a single configuration.

    """

    port_required = [ 'on_line', 'on_html_page' ]

    v2entry_points = [
        'do_download', 'do_get', 'do_poll', 'do_put', 'do_send', 'on_message',
        'on_file', 'on_heartbeat', 'on_housekeeping',
        'on_html_page', 'on_part', 'on_post', 'on_report',
        'on_start', 'on_stop', 'on_watch', 'plugin'
    ]
    components = [
        'audit', 'cpost', 'cpump', 'flow', 'poll', 'post', 'sarra', 'sender', 'shovel',
        'subscribe', 'sender', 'watch', 'winnow'
    ]

    actions = [
        'add', 'cleanup', 'convert', 'devsnap', 'declare', 'disable', 'dump', 'edit',
        'enable', 'foreground', 'log', 'list', 'remove', 'restart', 'sanity',
        'setup', 'show', 'start', 'stop', 'status', 'overview'
    ]

    # lookup in dictionary, respond with canonical version.
    appdir_stuff = {'appauthor': 'MetPX', 'appname': 'sr3'}

    # Correct name on the right, old name on the left.
    synonyms = {
        'accel_cp_threshold': 'accelThreshold',
        'accel_scp_threshold': 'accelThreshold',
        'accel_wget_threshold': 'accelThreshold',
        'accept_unmatch': 'acceptUnmatched',
        'accept_unmatched': 'acceptUnmatched',
        'basedir': 'baseDir',
        'base_dir': 'baseDir',
        'baseurl': 'baseUrl',
        'bind_queue': 'queueBind',
        'cache': 'nodupe_ttl',
        'declare_exchange': 'exchangeDeclare',
        'declare_queue': 'queueDeclare',
        'document_root': 'documentRoot',
        'caching': 'nodupe_ttl',
        'cache_basis': 'nodupe_basis',
        'e' : 'fileEvents',
        'events' : 'fileEvents',
        'exchange_split': 'exchangeSplit',
        'exchange_suffix': 'exchangeSuffix',
        'instance': 'instances',
        'chmod': 'permDefault',
        'default_mode': 'permDefault',
        'chmod_dir': 'permDirDefault',
        'default_dir_mode': 'permDirDefault',
        'chmod_log': 'permLog',
        'default_log_mode': 'permLog',
        'file_time_limit' : 'nodupe_fileAgeMax', 
        'heartbeat': 'housekeeping',
        'hb_memory_baseline_file' : 'MemoryBaseLineFile',
        'hb_memory_max' : 'MemoryMax',
        'hb_memory_multiplier' : 'MemoryMultiplier',
        'log_format': 'logFormat',
        'll': 'logLevel',
        'loglevel': 'logLevel',
        'log_reject': 'logReject',
        'logdays': 'logRotateCount',
        'log_rotate': 'logRotateCount',
        'logRotate': 'logRotateCount',
        'logRotate': 'logRotateCount',
        'logRotate_interval': 'logRotateInterval',
        'msg_replace_new_dir' : 'pathReplace',
        'msg_filter_wmo2msc_replace_dir': 'filter_wmo2msc_replace_dir',
        'msg_filter_wmo2msc_uniquify': 'filter_wmo2msc_uniquify',
        'msg_filter_wmo2msc_tree': 'filter_wmo2msc_treeify',
        'msg_filter_wmo2msc_convert': 'filter_wmo2msc_convert',
        'msg_fdelay' : 'fdelay',
        'no_duplicates': 'nodupe_ttl',
        'post_base_dir': 'post_baseDir',
        'post_basedir': 'post_baseDir',
        'post_base_url': 'post_baseUrl',
        'post_baseurl': 'post_baseUrl',
        'post_document_root': 'post_documentRoot',
        'post_exchange_split': 'post_exchangeSplit',
        'post_exchange_suffix': 'post_exchangeSuffix',
        'post_rate_limit': 'messageRateMax',
        'post_topic_prefix' : 'post_topicPrefix',
        'preserve_mode' : 'permCopy',
        'preserve_time' : 'timeCopy',
        'queue_name' : 'queueName', 
        'report_back': 'report',
        'source_from_exchange': 'sourceFromExchange', 
        'sum' : 'integrity',  
        'suppress_duplicates' : 'nodupe_ttl',
        'suppress_duplicates_basis' : 'nodupe_basis', 
        'tls_rigour' : 'tlsRigour', 
        'topic_prefix' : 'topicPrefix'
    }
    credentials = None

    def __init__(self, parent=None) -> 'Configuration':
        """
          instantiate an empty Configuration
        """
        self.bindings = []
        self.__admin = None
        self.__broker = None
        self.__post_broker = None

        if Config.credentials is None:
            Config.credentials = sarracenia.credentials.CredentialDB()
            Config.credentials.read(get_user_config_dir() + os.sep +
                                    "credentials.conf")
        self.directory = None

        self.env = copy.deepcopy(os.environ)

        egdir = os.path.dirname(inspect.getfile(sarracenia.config.Config)) + os.sep + 'examples' 

        self.config_search_path = [ "." , get_user_config_dir(), egdir, egdir + os.sep + 'flow'  ]


        for k in default_options:
            setattr(self, k, default_options[k])

        if parent is not None:
            for i in parent:
                setattr(self, i, parent[i])

        self.bufsize = 1024 * 1024
        self.byteRateMax = 0

        self.nodupe_fileAgeMax = 0 # disabled.
        self.timezone = 'UTC'
        self.debug = False
        self.declared_exchanges = []
        self.dry_run = False
        self.env_declared = []  # list of variable that are "declared env"'d 
        self.v2plugins = {}
        self.v2plugin_options = []
        self.imports = []
        self.logEvents = set(['after_accept', 'after_work', 'on_housekeeping' ])
        self.destfn_scripts = []
        self.plugins_late = []
        self.plugins_early = []
        self.exchange = None
        self.filename = None
        self.fixed_headers = {}
        self.flatten = '/'
        self.hostname = socket.getfqdn()
        self.hostdir = socket.getfqdn().split('.')[0]
        self.log_flowcb_needed = False
        self.sleep = 0.1
        self.housekeeping = 300
        self.inline = False
        self.inlineByteMax = 4096
        self.inlineEncoding = 'guess'
        self.integrity_arbitrary_value = None
        self.logReject = False
        self.logRotateCount = 5
        self.logRotateInterval = 1
        self.masks = []
        self.instances = 1
        self.mirror = False
        self.messageAgeMax = 0
        self.post_exchanges = []
	#self.post_topicPrefix = None
        self.pstrip = False
        self.queueName = None
        self.randomize = False
        self.rename = None
        self.randid = "%04x" % randint(0, 65536)
        self.statehost = False
        self.settings = {}
        self.strip = 0
        self.timeout = 300
        self.tlsRigour = 'normal'
        self.topicPrefix = [ 'v03', 'post' ]
        self.undeclared = []
        self.declared_users = {}
        self.users = False
        self.vip = None

    def __deepcopy__(self, memo) -> 'Configuration':
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
                v2=[]
                for m in v:
                    v2.append(tuple(list(copy.deepcopy(m[0:3]))+ [m[3]] + list(copy.deepcopy(m[4:]))))

                setattr(result, k, v2)
            else:
                setattr(result, k, copy.deepcopy(v, memo))
        return result

    def _validate_urlstr(self, urlstr) -> tuple :
        """
           returns a tuple ( bool, expanded_url ) 
           the bool is whether the expansion worked, and the expanded_url is one with
           the added necessary authentication details from sarracenia.Credentials.

        """
        # check url and add credentials if needed from credential file
        ok, cred_details = Config.credentials.get(urlstr)
        if cred_details is None:
            logging.error("bad credential %s" % urlstr)
            # Callers expect that a Credential object will be returned
            cred_details = sarracenia.credentials.Credential()
            cred_details.url = urllib.parse.urlparse(urlstr)
            return False, cred_details
        return True, cred_details

    def applyComponentDefaults( self, component ):
        """
          overlay defaults options for the given component to the given configuration.
        """
        if component in ['post']:
            self.override(sarracenia.flow.post.default_options)
        elif component in ['poll']:
            self.override(sarracenia.flow.poll.default_options)
        elif component in ['sarra']:
            self.override(sarradefopts)
        elif component in ['sender']:
            self.override(sarracenia.flow.sender.default_options)
        elif component in ['subscribe']:
            self.override(sarracenia.flow.subscribe.default_options)
        elif component in ['watch']:
            self.override(sarracenia.flow.watch.default_options)

    @property
    def admin(self):
        return self.__admin

    @admin.setter
    def admin(self, v):
        if type(v) is str:
            ok, cred_details = self._validate_urlstr(v)
            if ok:
                self.__admin = cred_details
        else:
            self.__admin = v

    @property
    def broker(self):
        return self.__broker

    @broker.setter
    def broker(self, v):
        if type(v) is str:
            ok, cred_details = self._validate_urlstr(v)
            if ok:
                self.__broker = cred_details
        else:
            self.__broker = v

    @property
    def post_broker(self):
        return self.__post_broker

    @post_broker.setter
    def post_broker(self, v):
        if type(v) is str:
            ok, cred_details = self._validate_urlstr(v)
            if ok:
                self.__post_broker = cred_details
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
        if (('${BROKER_USER}' in word) and hasattr(self, 'broker') and self.broker is not None and
                self.broker.url is not None and hasattr(self.broker.url, 'username')):
            result = result.replace('${BROKER_USER}', self.broker.url.username)
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
                e = 'component'
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
        if re.compile('DESTFNSCRIPT=.*').match(fn):
            script=fn[13:]
            self.destfn_scripts.append(script)

        return (arguments[0], self.directory, fn, regex,
                option.lower() in ['accept', 'get'], self.mirror, self.strip,
                self.pstrip, self.flatten)

    def mask_ppstr(self, mask):
        """
           return a pretty print string version of the given mask, easier for humans to read.
        """
        pattern, maskDir, maskFileOption, mask_regexp, accepting, mirror, strip, pstrip, flatten = mask

        s = 'accept' if accepting else 'reject'
        if pstrip : strip=pstrip
        strip = '' if strip == 0 else f' strip:{strip}'
        fn = '' if (maskFileOption == 'WHATFN') else f' filename:{maskFileOption}'
        flatten = '' if flatten == '/' else f' flatten:{flatten}'
        w = 'with ' if fn or flatten or strip else ''
        return f'{s} {pattern} into {maskDir} {w}mirror:{mirror}{strip}{flatten}{fn}'

    def add_option(self, option, kind='list', default_value=None):
        """
           options can be declared in any plugin. There are various *kind* of options, where the declared type modifies the parsing.
           
           * 'count'      integer count type. 

           * 'duration'   a floating point number indicating a quantity of seconds (0.001 is 1 milisecond)
                          modified by a unit suffix ( m-minute, h-hour, w-week ) 

           * 'flag'       boolean (True/False) option.

           * 'float'      a simple floating point number.

           * 'list'       a list of string values, each succeeding occurrence catenates to the total.
                          all v2 plugin options are declared of type list.

           * 'set'        a set of string values, each succeeding occurrence is unioned to the total.

           * 'size'       integer size. Suffixes k, m, and g for kilo, mega, and giga (base 2) multipliers.

           * 'str'        an arbitrary string value, as will all of the above types, each 
                          succeeding occurrence overrides the previous one.
    
        """
        #Blindly add the option to the list if it doesn't already exist
        if not hasattr(self, option):
            setattr(self, option, default_value)

        # Retreive the 'new' option & enforce the correct type.
        v = getattr(self, option)

        if kind == 'count':
            count_options.append(option)
            if type(v) is not int:
                setattr(self, option, humanfriendly.parse_size(v))
        elif kind == 'duration':
            duration_options.append(option)
            if type(v) is not float:
                setattr(self, option, durationToSeconds(v,default_value))
        elif kind == 'flag':
            flag_options.append(option)
            if type(v) is not bool:
                setattr(self, option, isTrue(v))
        elif kind == 'float':
            float_options.append(option)
            if type(v) is not float:
                setattr(self, option, float(v))
        elif kind == 'list':  
            list_options.append( option )
            if type(v) is not list:
                setattr(self, option, [v])
        elif kind == 'set':  
            set_options.append(option)
            sv=set()
            if type(v) is list:
                sv=set(v)
            elif type(v) is set:
                sv=v
            elif type(v) is str:
                if v == 'None': 
                    delattr(self, option)
                else:
                    v=v.replace('|',',')
                    if ',' in v: 
                        sv=set(v.split(','))
                    else: 
                        sv=set([v])
            if hasattr(self, option):
                sv= getattr(self,option) | sv
            setattr(self, option, sv)

        elif kind == 'size':
            size_options.append(option)
            if type(v) is not int:
                setattr(self, option, humanfriendly.parse_size(v))

        elif kind == 'str':
            str_options.append(option)
            if v is None:
                setattr(self, option, None)
            elif type(v) is not str:
                setattr(self, option, str(v))
        else:
            logger.error('invalid kind: %s for option: %s, ignored' % ( kind, option ) )
            return

        logger.debug('%s declared as type:%s value:%s' % (option, type(getattr(self,option)), v))

    def dump(self):
        """ print out what the configuration looks like.
       """

        term = shutil.get_terminal_size((80, 20))

        # for python > 3.7
        #c = copy.deepcopy(self.dictify())
        # but older python needs:
        c = self.dictify()
        d={}
        for k in c:
            if k == 'masks':
                i=0
                d['masks'] = []
                while i < len(c['masks']):
                   d['masks'].append( self.mask_ppstr(c['masks'][i]) )
                   i+=1
            else:
                d[k] = copy.deepcopy(c[k])

        for omit in [ 'env' ] :
            del d[omit]

        for k in d:
            if type(d[k]) is sarracenia.credentials.Credential :
                d[k] = str(d[k])

        pprint.pprint( d, width=term.columns, compact=True )
        return

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

    
    def get_source_from_exchange(self,exchange):
        #self.logger.debug("%s get_source_from_exchange %s" % (self.program_name,exchange))

        source = None
        if len(exchange) < 4 or not exchange.startswith('xs_') : return source

        # check if source is a valid declared source user

        len_u   = 0
        try:
                # look for user with role source
                for u in self.declared_users :
                    if self.declared_users[u] != 'source' : continue
                    if exchange[3:].startswith(u) and len(u) > len_u :
                       source = u
                       len_u  = len(u)
        except: pass

        return source

 

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
        """
           based on the given configuration, fill in with defaults or guesses.
           sets self.exchange.
        """
        if not hasattr(self, 'exchange') or self.exchange is None:
            #if hasattr(self, 'post_broker') and self.post_broker is not None and self.post_broker.url is not None:
            #    self.exchange = 'xs_%s' % self.post_broker.url.username
            #else:
            if not hasattr(self.broker.url,'username') or ( self.broker.url.username == 'anonymous' ):
                self.exchange = 'xpublic'
            else:
                self.exchange = 'xs_%s' % self.broker.url.username

            if hasattr(self, 'exchangeSuffix'):
                self.exchange += '_%s' % self.exchangeSuffix

            if hasattr(self, 'exchangeSplit') and hasattr(
                    self, 'no') and (self.no > 0):
                self.exchange += "%02d" % self.no

    def _parse_binding(self, subtopic_string):
        """
         FIXME: see original parse, with substitions for url encoding.
                also should sqwawk about error if no exchange or topicPrefix defined.
                also None to reset to empty, not done.
       """
        if hasattr(self, 'broker') and self.broker is not None and self.broker.url is not None:
            self._resolve_exchange()

        if type(subtopic_string) is str:
            if not hasattr(self, 'broker') or self.broker is None or self.broker.url is None:
                logger.error( 'broker needed before subtopic' )
                return

            if self.broker.url.scheme == 'amq' :
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
        #logger.error('input value: %s' % value)

        if not value:
            value = self.integrity_method

        if (value in sarracenia.integrity.known_methods) or (
                value[0:4] == 'cod,'):
            self.integrity_method = value
            #logger.error('returning 1: %s' % value)
            return

        if (value[0:2] == 'z,'):
            value = value[2:]
            self.integrity_method = 'cod,'
        elif (value[0:2] == 'a,'):
            self.integrity_method = 'arbitrary' 
            self.integrity_arbitrary_value = value[2:]
        else:
            self.integrity_method = value

        if value in [ 'N', 'none' ]:
            self.integrity_method = None
            #logger.error('returning 1.1: %s' % 'none')
            return 

        for sc in sarracenia.integrity.Integrity.__subclasses__():
            #logger.error('against 3: %s' % sc.__name__.lower() )
            if self.integrity_method == sc.__name__.lower():
                #logger.error('returning 2: %s' % self.integrity_method)
                return
            if hasattr(sc, 'registered_as'):
                #logger.error('against 3: %s' % sc.registered_as() )

                if (sc.registered_as() == value):
                    self.integrity_method = sc.__name__.lower()
                    #logger.error('returning 3: %s' % self.integrity_method)
                    return
        # FIXME this is an error return case, how to designate an invalid checksum?
        self.integrity_method = 'invalid'
        #logger.error('returning 4: invalid' )

    def parse_file(self, cfg, component=None):
        """ add settings from a given config file to self 
       """
        if component:
            cfname = f'{component}/{cfg}'
        else:
            cfname = cfg

        logger.debug( f'looking for {cfg} (in {os.getcwd()}')

        if cfg[0] == os.sep:
            cfgfilepath=cfg
        else:
            cfgfilepath=None
            for d in self.config_search_path:
                 cfgfilepath=d + os.sep + cfg
                 if os.path.isfile( cfgfilepath ):
                     break

            if not cfgfilepath:
                 logger.error( f'failed to find {cfg}' )
                 return
            logger.debug( f'found {cfgfilepath}')

        lineno=0
        for l in open(cfgfilepath, "r").readlines():
            l = l.strip()
            lineno+=1
            line = l.split()

            #print('FIXME parsing %s:%d %s' % (cfg, lineno, line ))

            if (len(line) < 1) or (line[0].startswith('#')):
                continue

            k = line[0]
            if k in Config.synonyms:
                k = Config.synonyms[k]
            elif k == 'destination':
                if component == 'poll':
                    k = 'pollUrl'
                else:
                    k = 'remoteUrl'

            if (k in convert_to_v3): 
                self.log_flowcb_needed |= '_log' in k
                   
                if (len(line) > 1):
                    v = line[1].replace('.py', '', 1)
                    if (v in convert_to_v3[k]):
                        line = convert_to_v3[k][v]
                        k = line[0]
                        if 'continue' in line:
                            logger.debug( f'{cfname}:{lineno} obsolete v2: \"{l}\" ignored' )
                        else:
                            logger.debug( f'{cfname}:{lineno} obsolete v2:\"{l}\" converted to sr3:\"{" ".join(line)}\"' )
                else:
                    line = convert_to_v3[k]
                    k=line[0]
                    v=line[1] 

            if k == 'continue':
                continue
            
            #FIXME: note for Clea, line conversion to v3 complete here.

            line = list(map(lambda x: self._varsub(x), line))

            if len(line) == 1:
                v = True
            else:
                v = line[1]

            # FIXME... I think synonym check should happen here, but no time to check right now.

            if k in flag_options:
                if len(line) == 1:
                    setattr(self, k, True)
                else:
                    setattr(self, k, isTrue(v))
                continue

            if len(line) < 2:
                logger.error('%s:%d %s missing argument(s) ' % ( cfname, lineno, k ) )
                continue
            if k in ['accept', 'reject', 'get']:
                self.masks.append(self._build_mask(k, line[1:]))
            elif k in [ 'callback', 'cb' ]:
                #vv = v.split('.')
                #v = 'sarracenia.flowcb.' + v + '.' + vv[-1].capitalize()
                if v not in self.plugins_late:
                    self.plugins_late.append(v)
            elif k in [ 'callback_prepend', 'cbp' ]:
                #vv = v.split('.')
                #v = 'sarracenia.flowcb.' + v + '.' + vv[-1].capitalize()
                if v not in self.plugins_early:
                    self.plugins_early.insert(0,v)
            elif k in ['declare']:
                self._parse_declare(line[1:])
            elif k in ['feeder']:
                self.feeder = urllib.parse.urlparse(line[1])
                self.declared_users[self.feeder.username] = 'feeder'
            elif k in ['header', 'h']:
                (kk, vv) = line[1].split('=')
                self.fixed_headers[kk] = vv
            elif k in ['include', 'config']:
                try:
                    self.parse_file(v)
                except Exception as ex:
                    logger.error('file %s failed to parse:  %s' % (v, ex))
                    logger.debug('Exception details: ', exc_info=True)
            elif k in ['subtopic']:
                self._parse_binding(v)
            elif k in ['topicPrefix']:
                if '/' in v :
                    self.topicPrefix = v.split('/')
                else:
                    self.topicPrefix = v.split('.')
            elif k in ['post_topicPrefix']:
                #if (not self.post_broker.url) or self.post_broker.url.scheme[0:3] == 'amq':
                if '/' in v :
                    self.post_topicPrefix = v.split('/')
                else:
                    self.post_topicPrefix = v.split('.')
            elif k in ['import']:
                self.imports.append(v)
            elif k in ['flow_callback', 'flowcb', 'fcb', 'flowCallback' ]:
                if v not in self.plugins_late:
                    self.plugins_late.append(v)
            elif k in ['flow_callback_prepend', 'flowcb_prepend', 'fcbp', 'flowCallbackPrepend' ]:
                if v not in self.plugins_early:
                    self.plugins_early.insert(0, v)
            elif k in ['set', 'setting', 's']:
                self._parse_setting(line[1], line[2:])
            elif k in ['integrity']:
                self._parse_sum(v)
            elif k in Config.port_required:
                logger.error( f' {cfname}:{lineno} {k} {v} not supported in v3, consult porting guide. Option ignored.' )
                logger.error( f' porting guide: https://github.com/MetPX/sarracenia/blob/v03_wip/docs/How2Guides/v2ToSr3.rst ' )
                continue
            elif k in Config.v2entry_points:
                #if k in self.plugins:
                #    self.plugins.remove(v)
                self._parse_v2plugin(k, v)
            elif k in ['no-import']:
                self._parse_v3unplugin(v)
            elif k in ['inflight', 'lock']:
                if v[:-1].isnumeric():
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
                        '%s:%d  %s is a duration option requiring a decimal number of seconds value'
                        % ( cfname, lineno, line[0]) )
                    continue
                setattr(self, k, durationToSeconds(v))
            elif k in float_options:
                try:
                    setattr(self, k, float(v))
                except (ValueError, TypeError) as e:
                    logger.error(f'Ignored "{i}": {e}')
            elif k in perm_options:
                if v.isdigit():
                    setattr(self, k, int(v, base=8))
                else:
                    logger.error('%s setting to %s ignored: only numberic modes supported' % ( k, v ) )
            elif k in size_options:
                setattr(self, k, humanfriendly.parse_size(v))
            elif k in count_options:
                setattr(self, k, humanfriendly.parse_size(v))
            elif k in list_options:
                if not hasattr(self, k):
                    setattr(self, k, [' '.join(line[1:])])
                else:
                    getattr(self, k).append(' '.join(line[1:]))
            elif k in set_options:
                vs = set(v.split(','))
                if v=='None':
                   setattr(self, k, set([]))
                   continue

                if not hasattr(self, k):
                    setattr(self, k, vs )
                else:
                    setattr(self, k, getattr(self, k) | vs)
                if hasattr(self, k) and (k in set_choices) :
                   for i in getattr(self,k):
                       if i not in set_choices[k]:
                          logger.error('invalid entry for %s:  %s. Must be one of: %s' % ( k, i, set_choices[k] ) )
            elif k in str_options:
                v = ' '.join(line[1:])
                setattr(self, k, v)
            else:
                #FIXME: with _options lists for all types and addition of declare, this is probably now dead code.
                logger.debug('possibly undeclared option: %s' % line )
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

        self._parse_sum(None)

        if hasattr(self, 'nodupe_ttl'):
            if (type(self.nodupe_ttl) is str):
                if isTrue(self.nodupe_ttl):
                    self.nodupe_ttl = 300
                else:
                    self.nodupe_ttl = durationToSeconds(
                        self.nodupe_ttl, default=300)
        else:
            self.nodupe_ttl = 0

        if self.debug:
            self.logLevel = 'debug'

        # double check to ensure duration options are properly parsed
        for d in duration_options:
            if hasattr(self, d) and (type(getattr(self, d)) is str):
                setattr(self, d, durationToSeconds(getattr(self, d)))

        if hasattr(self, 'kbytes_ps'):
            bytes_ps = humanfriendly.parse_size(self.kbytes_ps)
            if not self.kbytes_ps[-1].isalpha():
                bytes_ps *= 1024
            setattr(self, 'byteRateMax', bytes_ps)

        for d in count_options:
            if hasattr(self, d) and (type(getattr(self, d)) is str):
                setattr(self, d, humanfriendly.parse_size(getattr(self, d)))

        for d in size_options:
            if hasattr(self, d) and (type(getattr(self, d)) is str):
                setattr(self, d, chunksize_from_str(getattr(self, d)))

        for f in flag_options:
            if hasattr(self, f) and (type(getattr(self, f)) is str):
                setattr(self, f, isTrue(getattr(self, f)))

        for f in float_options:
            if hasattr(self, f) and (type(getattr(self, f)) is str):
                setattr(self, f, float(getattr(self, f)))

        if hasattr(self,'logReject'):
            if self.logReject:
                self.logEvents |= set( ['reject'] )

        if ( (len(self.logEvents) > 0 ) or self.log_flowcb_needed) :
            if ('sarracenia.flowcb.log.Log' not in self.plugins_late) and \
               ('log' not in self.plugins_late) :
                self.plugins_late.append( 'log' )

        # patch, as there is no 'none' level in python logging module...
        #    mapping so as not to break v2 configs.
        if hasattr(self, 'logLevel'):
            if self.logLevel == 'none':
                self.logLevel = 'critical'

        if hasattr(self, 'nodupe_basis'):
            if self.nodupe_basis == 'data': 
                self.plugins_early.append( 'nodupe.data' )
            elif self.nodupe_basis == 'name': 
                self.plugins_early.append( 'nodupe.name' )
            delattr( self, 'nodupe_basis' )

        # FIXME: note that v2 *user_cache_dir* is, v3 called:  cfg_run_dir
        if config[-5:] == '.conf':
            cfg = config[:-5]
        else:
            cfg = config

        if not hasattr(self, 'post_topicPrefix'):
           self.post_topicPrefix = self.topicPrefix

        if not hasattr(self, 'retry_ttl' ):
           self.retry_ttl = self.expire

        if self.retry_ttl == 0:
           self.retry_ttl = None

        if not hasattr(self, 'cfg_run_dir'):
            if self.statehost:
                hostdir = self.hostdir
            else:
                hostdir = None
            self.cfg_run_dir = os.path.join(get_user_cache_dir(hostdir),
                                            component, cfg)

        if self.post_broker is not None and self.post_broker.url is not None:
            if not hasattr(self,
                           'post_exchange') or self.post_exchange is None:
                self.post_exchange = 'xs_%s' % self.post_broker.url.username

            if hasattr(self, 'post_exchangeSuffix'):
                self.post_exchange += '_%s' % self.post_exchangeSuffix

            if hasattr(self, 'post_exchangeSplit'):
                l = []
                for i in range(0, int(self.post_exchangeSplit)):
                    y = self.post_exchange + '%02d' % i
                    l.append(y)
                self.post_exchange = l
            else:
                self.post_exchange = [self.post_exchange]

            if (component in ['poll' ]) and (hasattr(self,'vip') and self.vip):
                if (not hasattr(self,'exchange') or not self.exchange):
                    self.exchange = self.post_exchange[0]
                if (not hasattr(self,'broker') or not self.broker):
                    self.broker = self.post_broker

        if self.sourceFromExchange and self.exchange:
           self.source = self.get_source_from_exchange(self.exchange)

        if self.broker and self.broker.url and self.broker.url.username:
            self._resolve_exchange()

            queuefile = sarracenia.user_cache_dir(
                Config.appdir_stuff['appname'],
                Config.appdir_stuff['appauthor'])

            if self.statehost:
                queuefile += os.sep + self.hostdir

            queuefile += os.sep + component + os.sep + cfg
            queuefile += os.sep + component + '.' + cfg + '.' + self.broker.url.username

            if hasattr(self, 'exchangeSplit') and hasattr(
                    self, 'no') and (self.no > 0):
                queuefile += "%02d" % self.no
            queuefile += '.qname'

            self.queue_filename = queuefile

            while (not hasattr(self, 'queueName')) or (self.queueName is None):
                if os.path.isfile(queuefile):
                    f = open(queuefile, 'r')
                    self.queueName = f.read()
                    f.close()
                    #logger.info('FIXME: read queueName %s from queue state file' % self.queueName )
                    if len(self.queueName) < 1:
                          #logger.info('FIXME: queue name too short, try again' )
                          self.queueName=None
                if hasattr(self,'no') and self.no > 1:
                    time.sleep(randint(1,4))
                else:
                    break

            #if the queuefile is corrupt, then will need to guess anyways.
            if ( self.queueName is None ) or ( self.queueName == '' ):
                queueName = 'q_' + self.broker.url.username + '_' + component + '.' + cfg
                if hasattr(self, 'queue_suffix'):
                    queueName += '.' + self.queue_suffix
                queueName += '.' + str(randint(0, 100000000)).zfill(8)
                queueName += '.' + str(randint(0, 100000000)).zfill(8)
                self.queueName = queueName
                #logger.info('FIXME: defaulted queueName  %s ' % self.queueName )

                if not os.path.isdir(os.path.dirname(queuefile)):
                    pathlib.Path(os.path.dirname(queuefile)).mkdir(parents=True,
                                                                   exist_ok=True)

                # only lead instance (0-forground, 1-start, or none in the case of 'declare')
                # should write the state file.
                if (self.queueName is not None) and (not hasattr(self,'no') or (self.no < 2)):
                    f = open(queuefile, 'w')
                    f.write(self.queueName)
                    f.close()

        if hasattr(self, 'no'):
            if self.statehost:
                hostdir = self.hostdir
            else:
                hostdir = None
            self.pid_filename = get_pid_filename(hostdir, component, cfg,
                                                 self.no)
            self.retry_path = self.pid_filename.replace('.pid', '.retry')


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

        if hasattr(self, 'pollUrl'):
            if not hasattr(self,'post_baseUrl') or not self.post_baseUrl :
                logger.debug( f"defaulting post_baseUrl to match pollURl, since it isn't specified." )
                self.post_baseUrl = self.pollUrl
            
        # verify post_baseDir

        if self.post_baseDir is None:
            if self.post_documentRoot is not None:
                self.post_baseDir = self.post_documentRoot
                logger.warning("use post_baseDir instead of post_documentRoot")
            elif self.documentRoot is not None:
                self.post_baseDir = self.documentRoot
                logger.warning("use post_baseDir instead of documentRoot")
            elif self.baseDir is not None:
                self.post_baseDir = self.baseDir
                logger.debug("defaulting post_baseDir to same as baseDir")


        if self.messageCountMax > 0:
            if self.batch > self.messageCountMax:
                self.batch = self.messageCountMax
                logger.info(
                    'overriding batch for consistency with messageCountMax: %d'
                    % self.batch)
        if self.vip and not sarracenia.extras['vip']['present']:
            logger.critical( f"vip feature requested, but library: {' '.join(sarracenia.extras['vip']['modules_needed'])} " )
            sys.exit(1)

    def check_undeclared_options(self):

        alloptions = str_options + flag_options + float_options + list_options + set_options + count_options + size_options + duration_options
        # FIXME: confused about this...  commenting out for now...
        for u in self.undeclared:
            if u not in alloptions:
                logger.error("undeclared option: %s" % u)

        no_defaults=set()
        for u in alloptions:
             if not hasattr(self,u):
                no_defaults.add( u )

        logger.debug("missing defaults: %s" % no_defaults)

    """
      2020/05/26 FIXME here begins sheer terror.
      following routines are taken verbatim from v2. 
      trying not to touch it... it is painful.
      setting new_ values for downloading etc...
      sundew_* ... 
   """

    def _sundew_basename_parts(self, pattern, basename):
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

        BP = self._sundew_basename_parts(pattern, urlstr)

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

    def variableExpansion(self, cdir, message=None ):
        """
            replace substitution patterns, variable substitutions as described in
            https://metpx.github.io/sarracenia/Reference/sr3_options.7.html#variables

            examples:   ${YYYYMMDD-70m} becomes 20221107 assuming that was the current date 70 minutes ago.
                        environment variables, and built-in settings are replaced also.

           timeoffset -70m

        """

        if not '$' in cdir:
            return cdir

        new_dir = cdir

        if '${BD}' in cdir and self.baseDir != None:
            new_dir = new_dir.replace('${BD}', self.baseDir, 1)

        if ( '${BUP}' in cdir ) and ( 'baseUrl' in message ):
            u = urllib.parse.urlparse( message['baseUrl'] )
            new_dir = new_dir.replace('${BUP}', u.path, 1 )

        if ( '${baseUrlPath}' in cdir ) and ( 'baseUrl' in message ):
            u = urllib.parse.urlparse( message['baseUrl'] )
            new_dir = new_dir.replace('${baseUrlPath}', u.path, 1)

        if ( '${BUPL}' in cdir ) and ( 'baseUrl' in message ):
            u = urllib.parse.urlparse( message['baseUrl'] )
            new_dir = new_dir.replace('${BUPL}', os.path.basename(u.path), 1 )

        if ( '${baseUrlPathLast}' in cdir )  and ( 'baseUrl' in message ):
            u = urllib.parse.urlparse( message['baseUrl'] )
            new_dir = new_dir.replace('${baseUrlPathLast}', os.path.basename(u.path), 1 )

        if '${PBD}' in cdir and self.post_baseDir != None:
            new_dir = new_dir.replace('${PBD}', self.post_baseDir, 1)

        if '${DR}' in cdir and self.documentRoot != None:
            logger.warning(
                "DR = documentRoot should be replaced by BD for base_dir")
            new_dir = new_dir.replace('${DR}', self.documentRoot, 1)

        if '${PDR}' in cdir and self.post_baseDir != None:
            logger.warning(
                "PDR = post_documentRoot should be replaced by PBD for post_baseDir"
            )
            new_dir = new_dir.replace('${PDR}', self.post_baseDir, 1)

        whenStamp = time.mktime(time.gmtime()) + self.varTimeOffset

        if '${YYYYMMDD}' in cdir:
            YYYYMMDD = time.strftime("%Y%m%d", whenStamp)
            new_dir = new_dir.replace('${YYYYMMDD}', YYYYMMDD)

        if '${SOURCE}' in cdir:
            new_dir = new_dir.replace('${SOURCE}', message['source'])

        if '${DD}' in cdir:
            DD = time.strftime("%d", whenStamp)
            new_dir = new_dir.replace('${DD}', DD)

        if '${HH}' in cdir:
            HH = time.strftime("%H", whenStamp)
            new_dir = new_dir.replace('${HH}', HH)

        if '${YYYY}' in cdir:
            YYYY = time.strftime("%Y", whenStamp)
            new_dir = new_dir.replace('${YYYY}', YYYY)

        if '${MM}' in cdir:
            MM = time.strftime("%m", whenStamp)
            new_dir = new_dir.replace('${MM}', MM)

        if '${JJJ}' in cdir:
            JJJ = time.strftime("%j", whenStamp)
            new_dir = new_dir.replace('${JJJ}', JJJ)

        # Parsing cdir to subtract time from it in the following formats
        # time unit can be: sec/mins/hours/days/weeks

        # ${YYYY-[number][time_unit]}
        offset_check = re.search(r'\$\{YYYY-(\d+)(\D)\}', cdir)
        if offset_check:
            logger.info( f"offset 0: {offset_check.group(1,2)}" )
            seconds = durationToSeconds(''.join(offset_check.group(1, 2)),
                                             's')

            epoch = time.mktime(time.gmtime()) - seconds
            YYYY1D = time.strftime("%Y", time.localtime(epoch))
            new_dir = re.sub('\$\{YYYY-\d+\D\}', YYYY1D, new_dir)

        # ${MM-[number][time_unit]}
        offset_check = re.search(r'\$\{MM-(\d+)(\D)\}', cdir)
        if offset_check:
            logger.info( f"offset 1: {offset_check.group(1,2)}" )
            seconds = durationToSeconds(''.join(offset_check.group(1, 2)),
                                             's')

            epoch = time.mktime(time.gmtime()) - seconds
            MM1D = time.strftime("%m", time.localtime(epoch))
            new_dir = re.sub('\$\{MM-\d+\D\}', MM1D, new_dir)

        # ${JJJ-[number][time_unit]}
        offset_check = re.search(r'\$\{JJJ-(\d+)(\D)\}', cdir)
        if offset_check:
            logger.info( f"offset 2: {offset_check.group(1,2)}" )
            seconds = durationToSeconds(''.join(offset_check.group(1, 2)),
                                             's')

            epoch = time.mktime(time.gmtime()) - seconds
            JJJ1D = time.strftime("%j", time.localtime(epoch))
            new_dir = re.sub('\$\{JJJ-\d+\D\}', JJJ1D, new_dir)

        # ${YYYYMMDD-[number][time_unit]}
        offset_check = re.search(r'\$\{YYYYMMDD-(\d+)(\D)\}', cdir)
        if offset_check:
            logger.info( f"offset 3: {offset_check.group(1,2)}" )
            seconds = durationToSeconds(''.join(offset_check.group(1, 2)),
                                             's')
            epoch = time.mktime(time.gmtime()) - seconds
            YYYYMMDD = time.strftime("%Y%m%d", time.localtime(epoch))
            logger.info( f"seconds: {seconds} YYYYMMDD {YYYYMMDD}" )
            new_dir = re.sub('\$\{YYYYMMDD-\d+\D\}', YYYYMMDD, new_dir)

        new_dir = self._varsub(new_dir)

        return new_dir


    """
       2020/05/26 PAS... FIXME: end of sheer terror. 

       the parts below used be part of the sheer terror... but have been
       tamed a bit.
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
                raise Exception('broker needed before subtopic')
                return

            if not hasattr(namespace, 'exchange'):
                raise Exception('exchange needed before subtopic')
                return

            if not hasattr(namespace, 'topicPrefix'):
                raise Exception('topicPrefix needed before subtopic')
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
             description='version: %s\nSarracenia flexible tree copy ( https://MetPX.github.io/sarracenia ) ' % sarracenia.__version__ ,\
             formatter_class=argparse.ArgumentDefaultsHelpFormatter )

        if sys.version_info[0] >= 3 and sys.version_info[1] < 8:
            parser.register('action', 'extend', ExtendAction)
        
        parser.add_argument('--acceptUnmatched',
                            default=self.acceptUnmatched,
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

           -- sizing units,  K, M, G,  (should have humanfriendly based parsing.)
           -- time units s,h,m,d 
           -- what to do with verbs.
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
                            help='print debugging output (very verbose)')
        parser.add_argument('--dry_run', '--simulate', '--simulation', 
                            action='store_true',
                            default=self.dry_run,
                            help='simulation mode (perform no file transfers, just print what would happen)')
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
            '--inlineEncoding',
            choices=['text', 'binary', 'guess'],
            default=self.inlineEncoding,
            help='encode payload in base64 (for binary) or text (utf-8)')
        parser.add_argument('--inlineByteMax',
                            type=int,
                            default=self.inlineByteMax,
                            help='maximum message size to inline')
        parser.add_argument(
            '--instances',
            type=int,
            help='number of processes to run per configuration')

        parser.add_argument('--integrity_method', '--integrity', '-s', '--sum',
                            nargs='?',
                            default=self.integrity_method,
                            help='choose a different checksumming method for the files posted')
        if hasattr(self, 'bindings'):
            parser.set_defaults(bindings=self.bindings)

        parser.add_argument(
            '--logLevel',
            choices=[
                'notset', 'debug', 'info', 'warning', 'error', 'critical'
            ],
            help='encode payload in base64 (for binary) or text (utf-8)')
        parser.add_argument('--logReject',
                            action='store_true',
                            default=self.logReject,
                            help='print a log message explaining why each file is rejected')
        parser.add_argument('--logStdout',
                            action='store_true',
                            default=False,
                            help='disable logging, everything to standard output/error')
        parser.add_argument('--no',
                            type=int,
                            help='instance number of this process')
        parser.add_argument('--queueName',
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
            '--post_exchangeSplit',
            type=int,
            nargs='?',
            help='split output into different exchanges 00,01,...')
        parser.add_argument(
            '--post_topicPrefix',
            nargs='?',
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
        parser.add_argument(
            '--topicPrefix',
            nargs='?',
            default=self.topicPrefix,
            help=
            'allows simultaneous use of multiple versions and types of messages'
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
    if sarracenia.extras['amqp']['present']:
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
    if sarracenia.extras['amqp']['present']:
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
    #default_cfg.override(  { 'component':component, 'directory': os.getcwd(), 'acceptUnmatched':True, 'no':0 } )
    default_cfg.override({
        'component': component,
        'config': config,
        'acceptUnmatched': True,
        'no': 0
    })

    cfg = copy.deepcopy(default_cfg)

    cfg.applyComponentDefaults( component )

    store_pwd = os.getcwd()

    os.chdir(get_user_config_dir())
    os.chdir(component)

    if config[-5:] != '.conf':
        fname = config + '.conf'
    else:
        fname = config

    if os.path.exists(fname):
         cfg.parse_file(fname,component)
    else:
         logger.error('config %s not found' % fname )
         return None

    os.chdir(store_pwd)

    cfg.parse_args(isPost)

    #logger.error( 'after args' )
    #print( 'after args' )
    #cfg.dump()
    if component in ['poll' ]:
        if not hasattr(cfg,'broker') or (cfg.broker is None):
             cfg.broker = cfg.post_broker

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

def cfglogs(cfg_preparse, component, config, logLevel, child_inst):

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

        logfilename = get_log_filename(
            hostdir, component, config, child_inst)

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
        logger.setLevel(logLevel.upper())

        handler = sarracenia.instance.RedirectedTimedRotatingFileHandler(
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
        try:
            logger.setLevel(logLevel)
        except Exception:
            logger.setLevel(logging.INFO)

# add directory to python front of search path for plugins.
plugin_dir = get_user_config_dir() + os.sep + "plugins"
if os.path.isdir(plugin_dir) and not plugin_dir in sys.path:
    sys.path.insert(0, plugin_dir)
