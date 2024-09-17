# This file is part of Sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Shared Services Canada, 2019
#
r"""

Second version configuration parser

FIXME: pas 2023/02/05...  missing options from v2: max_queue_size, outlet, pipe

"""

import argparse
import copy
import datetime
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
from sarracenia.featuredetection import features
import sarracenia.credentials
import sarracenia.flow
import sarracenia.flowcb

from sarracenia.flow.sarra import default_options as sarradefopts

import sarracenia.identity.arbitrary

import sarracenia.moth
import sarracenia.identity
import sarracenia.instance


class octal_number(int):

    def __new__(cls, value):
        if type(value) is str:
            self = int(value,base=8)
        elif type(value) is int:
            self = value
        return self

    def __str__(self) -> str:
        return f"0o{self:o}"

    def __repr__(self) -> str:
        return f"0o{self:o}"


default_options = {
    'acceptSizeWrong': False,
    'acceptUnmatched': True,
    'amqp_consumer': False,
    'attempts': 3,
    'batch' : 100,
    'baseDir': None,
    'baseUrl_relPath': False,
    'delete': False,
    'documentRoot': None,
    'download': False,
    'dry_run': False,
    'filename': None,
    'flowMain': None,
    'inflight': None,
    'inline': False,
    'inlineOnly': False,
    'identity_method': 'sha512',
    'logFormat': '%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s',
    'logMetrics': False,
    'logStdout': False,
    'metrics_writeInterval': 5,
    'nodupe_driver': 'disk',
    'nodupe_ttl': 0,
    'overwrite': True,
    'path': [],
    'permDefault' : octal_number(0),
    'permDirDefault' : octal_number(0o775),
    'permLog': octal_number(0o600),
    'post_documentRoot': None,
    'post_baseDir': None,
    'post_baseUrl': None,
    'post_format': 'v03',
    'realpathPost': False,
    'recursive' : True,
    'runStateThreshold_reject': 80,
    'report': False,
    'retryEmptyBeforeExit': False,
    'retry_refilter': False,
    'runStateThreshold_cpuSlow': 0,
    'runStateThreshold_hung': 450,
    'runStateThreshold_idle': 900,
    'runStateThreshold_lag': 30,
    'runStateThreshold_retry': 1000,
    'runStateThreshold_slow': 0,
    'sourceFromExchange': False,
    'sourceFromMessage': False,
    'sundew_compat_regex_first_match_is_zero': False,
    'topicCopy': False,
    'v2compatRenameDoublePost': False,
    'varTimeOffset': 0,
    'wololo': False
}

count_options = [
    'batch', 'count', 'exchangeSplit', 'instances', 'logRotateCount', 'no', 
    'post_exchangeSplit', 'prefetch', 'messageCountMax', 'runStateThreshold_cpuSlow', 
    'runStateThreshold_reject', 'runStateThreshold_retry', 'runStateThreshold_slow', 
]


# all the boolean settings.
flag_options = [ 'acceptSizeWrong', 'acceptUnmatched', 'amqp_consumer', 'baseUrl_relPath', 'debug', \
    'delete', 'discard', 'download', 'dry_run', 'durable', 'exchangeDeclare', 'exchangeSplit', 'logReject', 'realpathFilter', \
    'follow_symlinks', 'force_polling', 'inline', 'inlineOnly', 'inplace', 'logMetrics', 'logStdout', 'logReject', 'restore', \
    'messageDebugDump', 'mirror', 'timeCopy', 'notify_only', 'overwrite', 'post_on_start', \
    'permCopy', 'persistent', 'queueBind', 'queueDeclare', 'randomize', 'recursive', 'realpathPost', \
    'reconnect', 'report', 'reset', 'retry_refilter', 'retryEmptyBeforeExit', 'save', 
    'sundew_compat_regex_first_match_is_zero', 'sourceFromExchange', 'sourceFromMessage', 'topicCopy', 
    'statehost', 'users', 'v2compatRenameDoublePost', 'wololo'
                ]

float_options = [ 'messageRateMax', 'messageRateMin' ]

duration_options = [
    'expire', 'housekeeping', 'logRotateInterval', 'fileAgeMax', 'fileAgeMin', 
    'messageAgeMax', 'post_messageAgeMax', 'metrics_writeInterval', \
    'runStateThreshold_idle', 'runStateThreshold_lag', 'retry_ttl', 'runStateThreshold_hung', 'sleep', 'timeout', 'varTimeOffset'
]

list_options = [ 'path', 'vip' ]

# set, valid values of the set.
set_options = [ 'logEvents', 'fileEvents' ]

set_choices = { 
    'logEvents' : set(sarracenia.flowcb.entry_points + [ 'reject' ]),
    'fileEvents' : set( [ 'create', 'delete', 'link', 'mkdir', 'modify', 'rmdir' ] )
 }
# FIXME: doesn't work... wonder why?
#    'fileEvents': sarracenia.flow.allFileEvents
 
perm_options = [ 'permDefault', 'permDirDefault','permLog']

size_options = ['accelThreshold', 'blockSize', 'bufSize', 'byteRateMax', 'fileSizeMax', 'inlineByteMax']

str_options = [
    'action', 'admin', 'baseDir', 'broker', 'cluster', 'directory', 'exchange',
    'exchange_suffix', 'feeder', 'filename', 'flatten', 'flowMain', 'header', 
    'hostname', 'identity', 'inlineEncoding', 'logFormat', 'logLevel', 
    'pollUrl', 'post_baseUrl', 'post_baseDir', 'post_broker', 'post_exchange',
    'post_exchangeSuffix', 'post_format', 'post_topic', 'queueName', 'queueShare', 'sendTo', 'rename',
    'report_exchange', 'source', 'strip', 'timezone', 'nodupe_ttl', 'nodupe_driver', 
    'nodupe_basis', 'tlsRigour', 'topic'
]

r"""
   for backward compatibility, 

   convert some old plugins that are hard to get working with
   v2wrapper, into v3 plugin.

   the fdelay ones makes in depth use of sr_replay function, and
   that has changed in v3 too much.

   accelerators and rate limiting are now built-in, no plugin required.
"""

convert_to_v3 = {
    'cache_stat' : ['continue'],
    'cluster_aliases' : [ 'continue' ],
    'discard' : [ 'delete_destination', 'on' ], 
    'from_cluster' : [ 'continue' ],
    'to_clusters' : [ 'continue' ],
    'identity' : {
       'n' : [ 'identity', 'none' ],
       's' : [ 'identity', 'sha512' ],
       'd' : [ 'identity', 'md5' ],
       'a' : [ 'identity', 'arbitrary' ],
       'r' : [ 'identity', 'random' ],
       'z,d' : [ 'identity', 'cod,md5' ],
       'z,s' : [ 'identity', 'cod,sha512' ],
       'z,n' : [ 'identity', 'none' ]
    },
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
    'destfn_script': { 'manual_conversion_required' : [ 'continue' ] },
    'do_get': { 'manual_conversion_required' : [ 'continue' ] },
    'do_poll': { 'manual_conversion_required' : [ 'continue' ] },
    'do_put': { 'manual_conversion_required' : [ 'continue' ] },
    'do_download': { 'manual_conversion_required' : [ 'continue' ] },
    'do_put': { 'manual_conversion_required' : [ 'continue' ] },
    'do_send': {
       'file_email' : [ 'callback', 'send.email' ],
    },
    'do_task': { 'manual_conversion_required' : [ 'continue' ] },
    'no_download': [ 'download', 'False' ],
    'notify_only': [ 'download', 'False' ],
    'do_data': { 'manual_conversion_required' : [ 'continue' ] },
    'on_file': {
        'file_age' : [ 'callback', 'work.age' ],
    },
    'on_heartbeat': { 'manual_conversion_required' : [ 'continue' ] },
    'on_html_page': { 'manual_conversion_required' : [ 'continue' ] },
    'on_part': { 'manual_conversion_required' : [ 'continue' ] },
    'on_line': { 'manual_conversion_required' : [ 'continue' ] },
    'on_message': {
    	'msg_by_source': ['continue'],
    	'msg_by_user': ['continue'],
        'msg_delete': [ 'callback', 'filter.deleteflowfiles.DeleteFlowFiles'],
    	'msg_download': ['continue'],
    	'msg_dump': ['continue'],
        'msg_log': ['logEvents', '+after_accept'],
        'msg_print_lag': [ 'callback', 'accept.printlag.PrintLag'],
        'msg_rawlog': ['logEvents', '+after_accept'],
    	'msg_total': ['continue'],
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
    },
    'on_report': { 'manual_conversion_required' : [ 'continue' ] },
    'on_stop':   { 'manual_conversion_required' : [ 'continue' ] },
    'on_start':  { 'manual_conversion_required' : [ 'continue' ] },
    'on_watch':  { 'manual_conversion_required' : [ 'continue' ] },
    'on_post': {
        'post_log': ['logEvents', '+after_work'],
	    'post_total': ['continue'],
        'wmo2msc': [ 'callback', 'filter.wmo2msc.Wmo2Msc'],
        'post_hour_tree': [ 'callback', 'accept.posthourtree.PostHourTree'],
        'post_long_flow': [ 'callback', 'accept.longflow.LongFLow'],
        'post_override': [ 'callback', 'accept.postoverride.PostOverride'],
	    'post_rate_limit': ['continue'],
        'to': ['continue']
    },
    'parts' : [ 'continue' ],
    'poll_without_vip': [ 'manual_conversion_required' ], 
    'pump' : [ 'continue' ],
    'pump_flag' : [ 'continue' ],
    'reconnect': ['continue'],
    'report_daemons': ['continue'],
    'restore' : [ 'continue' ],
    'retry_mode' : ['continue'],
    'save' : [ 'continue' ],
    'set_passwords': ['continue'],
    'windows_run': [ 'continue' ],
    'xattr_disable': [ 'continue' ]
}

# question: why don't these have matching closing braces? 
# answer: there might be an offset (-1h, -5m, etc...) and covering those cases is hard with simple substitution.

convert_patterns_to_v3 = {
   '${YYYYMMDD-1D' : '${%o-1d%Y%m%d',
   '${YYYYMMDD-2D' : '${%o-2d%Y%m%d',
   '${YYYYMMDD' : '${%Y%m%d',
   '${YYYY': '${%Y',
   '${JJJ': '${%j',
   '${HH': '${%H',
   '${DD': '${%d',
   '${MM': '${%m',
   '${SS': '${%S',

}

logger = logging.getLogger(__name__)

r"""
   FIXME: respect appdir stuff using an environment variable.
   for not just hard coded as a class variable appdir_stuff

"""


def isTrue(S):
    if type(S) is list:
        S = S[-1]
    return S.lower() in ['true', 'yes', 'on', '1']

def parse_count(cstr):
    """
        number argument accepts k,m,g suffix with i and b to use base 2 ) and +- 
        return value is integer.
    """
    if cstr[0] == '-':
        offset=1
    else:
        offset=0
    try:
        count=humanfriendly.parse_size(cstr[offset:], binary=cstr[-1].lower() in ['i','b'] )
        return -count if offset else count
    except Exception as Ex:
        logger.error( f"failed to parse:  {cstr} as a count value" )
        logger.debug('Exception details: ', exc_info=True)
        return 0

def parse_float(cstr):
    """
        like parse_count, numeric argument accepts k,m,g suffix and +-.
        below 1000, return a decimal number with 3 digits max.
    """
    if type(cstr) is not str:
        return cstr

    try:
        fa = parse_count(cstr)
        if abs(fa) < 1000:
            if cstr[-1] in [ 'b', 'i' ]:
                if cstr[-2] in [ 'k' ]:
                    fa=float(cstr[0:-2])*1024
                else:
                    fa=float(cstr[0:-1])
            elif cstr[-1] in [ 'k' ]:
                    fa=float(cstr[0:-1])*1000
            else:
                fa=float(cstr)

            # apply 3 sig figs.
            if abs(fa) > 1000:
                fa=int(fa)
            elif abs(fa) > 100:
                fa=round(fa,1)
            elif abs(fa) > 10:
                fa=round(fa,2)
            else:
                fa=round(fa,3)

        return fa
    except Exception as Ex:
        logger.error( f"failed to parse:  {cstr} as a float value" )
        logger.debug('Exception details: ', exc_info=True)
        return 0.0

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

def get_metrics_filename(hostdir, component, configuration, no):
    """
      return the name of a single logfile for a single instance.
   """
    metricsdir = get_user_cache_dir(hostdir) + os.sep + 'metrics'

    if configuration is None:
        configuration = ''
    else:
        configuration = '_' + configuration

    if configuration[-5:] == '.conf':
        configuration = configuration[:-5]

    return metricsdir + os.sep + component + configuration + '_%02d' % no + '.json'

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
    r"""
       The option parser to produce a single configuration.

       it can be instantiated with one of:

       * one_config(component, config, action, isPost=False) -- read the options  for
         a given component an configuration,  (all in one call.)

       On the other hand, a configu can be built up from the following constructors:

       * default_config() -- returns an empty configuration, given a config file tree.
       * no_file_config() -- returns an empty config without any config file tree. 

       Then just add settings manually::

         cfg = no_file_config()

         cfg.broker = sarracenia.credentials.Credential('amqps://anonymous:anonymous@hpfx.collab.science.gc.ca')
         cfg.topicPrefix = [ 'v02', 'post']
         cfg.component = 'subscribe'
         cfg.config = 'flow_demo'
         cfg.action = 'start'
         cfg.bindings = [ ('xpublic', ['v02', 'post'], ['*', 'WXO-DD', 'observations', 'swob-ml', '#' ]) ]
         cfg.queueName='q_anonymous.subscriber_test2'
         cfg.download=True
         cfg.batch=1
         cfg.messageCountMax=5
       
         # set the instance number for the flow class.
         cfg.no=0
       
       # and at the end call finalize

       cfg.finalize()

    """

    port_required = [ 'on_line', 'on_html_page' ]

    v2entry_points = [
        'do_download', 'do_get', 'do_poll', 'do_put', 'do_send', 'on_message',
        'on_file', 'on_heartbeat', 'on_housekeeping',
        'on_html_page', 'on_part', 'on_post', 'on_report',
        'on_start', 'on_stop', 'on_watch', 'plugin'
    ]
    components = [
        'cpost', 'cpump', 'flow', 'poll', 'post', 'sarra', 'sender', 'shovel',
        'subscribe', 'watch', 'winnow'
    ]

    actions = [
        'add', 'cleanup', 'convert', 'devsnap', 'declare', 'disable', 'dump', 'edit',
        'enable', 'features', 'foreground', 'log', 'list', 'remove', 'restart', 'run', 'sanity',
        'setup', 'show', 'start', 'stop', 'status', 'overview'
    ]

    # lookup in dictionary, respond with canonical version.
    appdir_stuff = {'appauthor': 'MetPX', 'appname': 'sr3'}

    # Correct name on the right, old name on the left.
    synonyms = {
        'a': 'action',
        'accel_cp_threshold': 'accelThreshold',
        'accel_scp_threshold': 'accelThreshold',
        'accel_wget_threshold': 'accelThreshold',
        'accept_unmatch': 'acceptUnmatched',
        'accept_unmatched': 'acceptUnmatched',
        'at': 'attempts', 
        'b': 'broker',
        'bd': 'baseDir',
        'basedir': 'baseDir',
        'base_dir': 'baseDir',
        'baseurl': 'baseUrl',
        'bind_queue': 'queueBind',
        'blocksize': 'blockSize', 
        'bufsize': 'bufSize',
        'cache': 'nodupe_ttl',
        'c': 'include',
        'cb': 'nodupe_basis',
        'cache_basis': 'nodupe_basis',
        'caching': 'nodupe_ttl',
        'chmod': 'permDefault',
        'chmod_dir': 'permDirDefault',
        'chmod_log': 'permLog',
        'content' : 'inline', 
        'content_encoding':  'inlineEncoding',
        'content_max': 'inlineByteMax',
        'd': 'discard',
        'declare_exchange': 'exchangeDeclare',
        'declare_queue': 'queueDeclare',
        'default_mode': 'permDefault',
        'default_dir_mode': 'permDirDefault',
        'default_log_mode': 'permLog',
        'destination_timezone': 'timezone', 
        'document_root': 'documentRoot',
        'download-and-discard': 'discard',
        'e' : 'fileEvents',
        'events' : 'fileEvents',
        'ex': 'exchange',
        'exchange_split': 'exchangeSplit',
        'exchange_suffix': 'exchangeSuffix',
        'expiry': 'expire', 
        'file_time_limit' : 'fileAgeMax', 
        'nodupe_fileAgeMax' : 'fileAgeMax', 
        'nodupe_fileAgeMin' : 'fileAgeMin', 
        'fp' : 'force_polling',
        'fs' : 'follow_symlinks',
        'h' : 'help',
        'heartbeat': 'housekeeping',
        'hb_memory_baseline_file' : 'MemoryBaseLineFile',
        'hb_memory_max' : 'MemoryMax',
        'hb_memory_multiplier' : 'MemoryMultiplier',
        'imx': 'inlineByteMax',
        'inl' : 'inline', 
        'inline_encoding':  'inlineEncoding',
        'inline_max': 'inlineByteMax',
        'instance': 'instances',
        'lock': 'inflight', 
        'log_format': 'logFormat',
        'll': 'logLevel',
        'loglevel': 'logLevel',
        'log_reject': 'logReject',
        'logdays': 'logRotateCount',
        'log_rotate': 'logRotateCount',
        'logRotate': 'logRotateCount',
        'logRotate': 'logRotateCount',
        'logRotate_interval': 'logRotateInterval',
        'message-ttl': 'post_messageAgeMax',
        'message_ttl': 'post_messageAgeMax',
        'msg_replace_new_dir' : 'pathReplace',
        'msg_filter_wmo2msc_replace_dir': 'filter_wmo2msc_replace_dir',
        'msg_filter_wmo2msc_uniquify': 'filter_wmo2msc_uniquify',
        'msg_filter_wmo2msc_tree': 'filter_wmo2msc_treeify',
        'msg_filter_wmo2msc_convert': 'filter_wmo2msc_convert',
        'msg_fdelay' : 'fdelay',
        'n': 'no_download', 
        'nd': 'nodupe_ttl',
        'no_duplicates': 'nodupe_ttl',
        'o' : 'overwrite', 
        'on_msg': 'on_message',
        'p' : 'path',
        'pm' : 'permCopy',
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
        'pt' : 'timeCopy',
        'qn': 'queueName',
        'queue' : 'queueName', 
        'queue_name' : 'queueName', 
        'realpath' : 'realpathPost',
        'realpath_filter' : 'realpathFilter',
        'realpath_post' : 'realpathPost',
        'remoteUrl' : 'sendTo', 
        'report_back': 'report',
        'sanity_log_dead': 'runStateThreshold_hung',
        'sd' : 'nodupe_ttl',
        'sdb' : 'nodupe_basis', 
        'simulate': 'dry_run',
        'simulation': 'dry_run',
        'source_from_exchange': 'sourceFromExchange', 
        'sum' : 'identity',  
        'suppress_duplicates' : 'nodupe_ttl',
        'suppress_duplicates_basis' : 'nodupe_basis', 
        'tls_rigour' : 'tlsRigour', 
        'topic_prefix' : 'topicPrefix'
    }
    credentials = None

    def __init__(self, parent=None) -> 'Config':
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

        self.bufSize = 1024 * 1024
        self.byteRateMax = 0

        self.fileAgeMax = 0 # disabled.
        self.fileAgeMin = 0 # disabled.
        self.timezone = 'UTC'
        self.debug = False
        self.declared_exchanges = []
        self.discard = False
        self.displayFull = False
        self.dry_run = False
        self.env_declared = []  # list of variable that are "declared env"'d 
        self.files = []
        self.lineno = 0
        self.v2plugins = {}
        self.v2plugin_options = []
        self.imports = []
        self.logEvents = set(['after_accept', 'after_post', 'after_work', 'on_housekeeping' ])
        self.destfn_scripts = []
        self.plugins_late = []
        self.plugins_early = []
        self.exchange = None
        self.fileSizeMax = 0
        self.filename = None
        self.fixed_headers = {}
        self.flatten = '/'
        self.hostname = socket.getfqdn()

        # oddness where final period is included in hostname...seems wrong. happens on windows a lot.
        if self.hostname[-1] == '.':
            self.hostname = self.hostname[0:-1]
        self.hostdir = socket.getfqdn().split('.')[0]
        self.log_flowcb_needed = False
        self.sleep = 0.1
        self.housekeeping = 300
        self.inline = False
        self.inlineByteMax = 4096
        self.inlineEncoding = 'guess'
        self.identity_arbitrary_value = None
        self.logReject = False
        self.logRotateCount = 5
        self.logRotateInterval = 60*60*24
        self.masks = []
        self.instances = 1
        self.mirror = False
        self.messageAgeMax = 0
        self.post_exchanges = []
        self.post_messageAgeMax = 0
	    #self.post_topicPrefix = None
        self.pstrip = False
        self.queueName = None
        self.queueShare = "${USER}_${HOSTNAME}_${RAND8}"
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
        self.vip = []

    def __deepcopy__(self, memo) -> 'Configuration':
        r"""
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
            logging.critical("bad credential %s" % urlstr)
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
        elif type(word) in [bool, int, float, octal_number]:
            return word
        elif not '$' in word:
            return word

        result = word
        if (('${BROKER_USER}' in word) and hasattr(self, 'broker') and self.broker is not None and
                self.broker.url is not None and hasattr(self.broker.url, 'username')):
            result = result.replace('${BROKER_USER}', self.broker.url.username)
            # FIXME: would this work also automagically if BROKER.USERNAME ?

        if (('${POST_BROKER_USER}' in word) and hasattr(self, 'post_broker') and self.post_broker is not None and
                self.post_broker.url is not None and hasattr(self.post_broker.url, 'username')):
            result = result.replace('${POST_BROKER_USER}', self.post_broker.url.username)

        if ( '${RAND8}' in word ):
            result = result.replace('${RAND8}', str(randint(0, 100000000)).zfill(8))

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
        try:
            regex = re.compile(arguments[0])
        except:
            logger.critical( f"{','.join(self.files)}{self.lineno} invalid regular expression: {arguments[0]}, ignored." )
            return None

        if len(arguments) > 1:
            fn = arguments[1]
        else:
            fn = self.filename
        if fn and re.compile('DESTFNSCRIPT=.*').match(fn):
            script=fn[13:]
            self.destfn_scripts.append(script)

        if self.directory:
           d = os.path.expanduser(self.directory)
        else:
           d = self.directory
        return (arguments[0], d, fn, regex,
                option.lower() in ['accept' ], self.mirror, self.strip,
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

    def _parse_set_string( self, v:str, old_value: set ) -> set:
        """
           given a set string, return a python set.
        """
        sv=set()
        if type(v) is list:
            sv=set(v)
        elif type(v) is set:
            sv=v
        elif type(v) is str:
            v=v.replace('|',',')
            if v == 'None': 
                sv=set([])
            else:
                op='r'
                while v[0] in [ '+', '-']:
                    op=v[0]
                    v=v[1:]

                if ',' in v: 
                    sv=set(v.split(','))
                else: 
                    sv=set([v])

                if op == '+':
                    sv= old_value | sv
                elif op == '-' :
                    sv= old_value - sv

        return sv

    def add_option(self, option, kind='list', default_value=None, all_values=None ):
        r"""
           options can be declared in any plugin. There are various *kind* of options, where the declared type modifies the parsing.
           
           * 'count'      integer count type. 

           * 'octal'      base-8 (octal) integer type.
           * 'duration'   a floating point number indicating a quantity of seconds (0.001 is 1 milisecond)
                          modified by a unit suffix ( m-minute, h-hour, w-week ) 

           * 'flag'       boolean (True/False) option.

           * 'float'      a simple floating point number.

           * 'list'       a list of string values, each succeeding occurrence catenates to the total.
                          all v2 plugin options are declared of type list.

           * 'set'        a set of string values, each succeeding occurrence is unioned to the total.
                          if all_values is provided, then constrain set to that.

           * 'size'       integer size. Suffixes k, m, and g for kilo, mega, and giga (base 2) multipliers.

           * 'str'        an arbitrary string value, as will all of the above types, each 
                          succeeding occurrence overrides the previous one.
    
           If a value is set to None, that could mean that it has not been set.
        """
        #Blindly add the option to the list if it doesn't already exist
        if not hasattr(self, option):
            setattr(self, option, default_value)

        # Retreive the 'new' option & enforce the correct type.
        v = getattr(self, option)

        if kind not in [ 'list', 'set' ] and type(v) == list:
            v=v[-1]
            logger.warning( f"{','.join(self.files)}{self.lineno} multiple declarations of {kind} {option}={getattr(self,option)} choosing last one: {v}" )


        if kind == 'count':
            count_options.append(option)
            if type(v) is not int:
                setattr(self, option, parse_count(v))
        elif kind == 'duration':
            duration_options.append(option)
            if type(v) is not float:
                setattr(self, option, durationToSeconds(v,default_value))
        elif kind == 'flag' or kind == bool:
            flag_options.append(option)
            if type(v) is not bool:
                setattr(self, option, isTrue(v))
        elif kind == 'float' or kind == float :
            float_options.append(option)
            if type(v) is not float:
                setattr(self, option, parse_float(v))
        elif kind == 'list' or kind == list:  
            list_options.append( option )
            if type(v) is not list:
                #subtlety... None means: has not been set, 
                # where an empty list to be an explicit setting.
                if v is None:
                    setattr(self, option, None)
                else:
                    setattr(self, option, [v])
        elif kind == 'octal':
            perm_options.append(option)
            if type(v) is not octal_number:
                setattr(self, option, octal_number(int(v,base=8)))
        elif kind == 'set':  
            set_options.append(option)
            sv = self._parse_set_string(v,set())
            setattr(self, option, sv)
            if all_values:
                set_choices[option] = all_values

        elif kind == 'size' or kind == int:
            size_options.append(option)
            if type(v) is not int:
                setattr(self, option, parse_count(v))

        elif kind == 'str' or kind == str:
            str_options.append(option)
            if v is None:
                setattr(self, option, None)
            elif type(v) is not str:
                setattr(self, option, str(v))
        else:
            logger.error( f"{','.join(self.files)}{self.lineno} invalid kind: {kind} for option: {option} ignored" )
            return

        logger.debug( f"{','.join(self.files)}{self.lineno} {option} declared as type:{type(getattr(self,option))} value:{v}" )

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
                logger.error( f"{','.join(self.files)}:{self.lineno} broker needed before subtopic" )
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
          * options = { 'level' : 'debug' }
    

       """
        opt_class = '.'.join(opt.split('.')[:-1])
        opt_var = opt.split('.')[-1]
        if opt_class not in self.settings:
            self.settings[opt_class] = {}

        self.settings[opt_class][opt_var] = ' '.join(value)

    def _parse_sum(self, value):
        #logger.error('FIXME! input value: %s' % value)

        if not value:
            if not self.identity_method:
               return
            value = self.identity_method

        if (value in sarracenia.identity.known_methods) or (
                value[0:4] == 'cod,'):
            self.identity_method = value
            #logger.error('returning 1: %s' % value)
            return

        #logger.error( f'1 value: {value} self.identity_method={self.identity_method}' )
        if (value[0:2] == 'z,'):
            value = value[2:]
            self.identity_method = 'cod,'
        elif (value[0:2] == 'a,'):
            self.identity_method = 'arbitrary' 
            self.identity_arbitrary_value = value[2:]
        else:
            self.identity_method = value
        #logger.error( f'2 value: {value} self.identity_method={self.identity_method}' )

        if value.lower() in [ 'n', 'none' ]:
            self.identity_method = None
            #logger.error('returning 1.1: %s' % 'none')
            return 
        #logger.error( f'3 value: {value} self.identity_method={self.identity_method}' )

        for sc in sarracenia.identity.Identity.__subclasses__():
            #logger.error('against 1.8: %s' % sc.__name__.lower() )
            if value == sc.__name__.lower():
                #logger.error('returning 2: %s' % value )
                if self.identity_method == 'cod,':
                      self.identity_method += value
                else:
                      self.identity_method = value
                return
            if hasattr(sc, 'registered_as'):
                #logger.error('against 3: %s' % sc.registered_as() )

                if (sc.registered_as() == value):
                    if self.identity_method == 'cod,':
                          self.identity_method += sc.__name__.lower()
                    else:
                          self.identity_method = sc.__name__.lower()
                    #logger.error('returning 3: %s' % self.identity_method)
                    return
        # FIXME this is an error return case, how to designate an invalid checksum?
        self.identity_method = 'invalid'
        #logger.error('returning 4: invalid' )




    def parse_file(self, cfg, component=None):
        """ add settings from a given config file to self 
       """
        if component:
            cfname = f'{component}/{cfg}'
        else:
            cfname = cfg

        logger.debug( f'looking for {cfg} (in {os.getcwd()}')

        cfg=os.path.expanduser(cfg)

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
        saved_lineno=0
        self.files.append(cfgfilepath)

        for l in open(cfgfilepath, "r").readlines():
            lineno+=1
            if self.lineno > 0:
               saved_lineno = self.lineno
            self.parse_line( component, cfg, cfname, lineno, l.strip() )

        self.files.pop()
        self.lineno = saved_lineno


    def parse_line(self, component, cfg, cfname, lineno, l ):
        self.lineno = lineno
        line = l.split()

        #print('FIXME parsing %s:%d %s' % (cfg, lineno, line ))

        if (len(line) < 1) or (line[0].startswith('#')):
            return

        k = line[0]
        if k in Config.synonyms:
            k = Config.synonyms[k]
        elif k == 'destination':
            if component == 'poll':
                k = 'pollUrl'
            else:
                k = 'sendTo'
        elif k == 'broker' and component == 'poll' :
            k = 'post_broker'

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
            return
            
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
            if k in ['logReject'] and self.logReject:
                self.logEvents = self.logEvents | set(['reject'])
            return

        if len(line) < 2:
            logger.error( f"{','.join(self.files)}:{lineno} {k} missing argument(s)" )
            return
        if k in ['accept', 'reject' ]:
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
        elif k in ['feeder', 'manager']:
            self.feeder = urllib.parse.urlparse(line[1])
            self.declared_users[self.feeder.username] = 'feeder'
        elif k in ['header', 'h']:
            (kk, vv) = line[1].split('=')
            self.fixed_headers[kk] = vv
        elif k in ['include', 'config']:
            try:
                self.parse_file(v)
            except Exception as ex:
                logger.error( f"{','.join(self.files)}:{self.lineno} file {v} failed to parse:  {ex}" )
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
        elif k in ['identity', 'integrity']:
            self._parse_sum(v)
        elif k in Config.port_required:
            logger.error( f' {cfname}:{lineno} {k} {v} not supported in v3, consult porting guide. Option ignored.' )
            logger.error( f' porting guide: https://github.com/MetPX/sarracenia/blob/v03_wip/docs/How2Guides/v2ToSr3.rst ' )
            return
        elif k in Config.v2entry_points:
            #if k in self.plugins:
            #    self.plugins.remove(v)
            self._parse_v2plugin(k, v)
        elif k in ['no-import']:
            self._parse_v3unplugin(v)
        elif k in ['inflight', 'lock']:
            if v[:-1].isnumeric():
                vv = durationToSeconds(v)
                setattr(self, k, vv)
                self.fileAgeMin = vv
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
                return
            setattr(self, k, durationToSeconds(v))
        elif k in float_options:
            try:
                setattr(self, k, parse_float(v))
            except (ValueError, TypeError) as e:
                logger.error(f"{','.join(self.files)}:{self.lineno} Ignored '{i}': {e}")
        elif k in perm_options:
            if v.isdigit():
                setattr(self, k, octal_number(int(v, base=8)))
            else:
                logger.error( f'{",".join(self.files)}:{lineno} {k} setting to {v} ignored: only numberic modes supported' )
        elif k in size_options:
            setattr(self, k, parse_count(v))
        elif k in count_options:
            setattr(self, k, parse_count(v))
        elif k in list_options:
            if not hasattr(self, k) or not getattr(self,k):
                setattr(self, k, [' '.join(line[1:])])
            else:
                l = getattr(self, k)
                l.append(' '.join(line[1:]))
        elif k in set_options:
            if v.lower() == 'none':
                setattr(self, k, set([]))
                return
            if v.lower() in [ 'all' , '+all' ]:
                if k in set_choices:
                    setattr(self,k,set_choices[k])
                return
            v=v.replace('|',',')
            vs = self._parse_set_string(v,getattr(self,k))
            setattr(self, k, vs )

            if k in set_choices :
                for i in getattr(self,k):
                    if i not in set_choices[k]:
                        logger.error( f'{",".join(self.files)}:{lineno} invalid entry {i} in {k}. Must be one of: {set_choices[k]}' )

        elif k in str_options:
            if ( k == 'directory' ) and not self.download:
                logger.info( f"{','.join(self.files)}:{lineno} if download is false, directory has no effect" )

            v = ' '.join(line[1:])
            if v == 'None':
                v=None
            setattr(self, k, v)
        else:
            #FIXME: with _options lists for all types and addition of declare, this is probably now dead code.
            if k not in self.undeclared:
                logger.debug( f'{",".join(self.files)}:{self.lineno} possibly undeclared option: {line}' )
            v = ' '.join(line[1:])
            if hasattr(self, k):
                if type(getattr(self, k)) is float:
                    setattr(self, k, parse_float(v))
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
                self.undeclared.append( (cfname, lineno, k) )

    def _resolveQueueName(self,component,cfg):

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

        #while (not hasattr(self, 'queueName')) or (self.queueName is None):
        """

          normal:
              if not the lead instance, wait a bit for the queuefile to be written.
              look for a queuefile in the state directory, if it is there, read it.
              if you can't read the file

          if you are instance 1, or 0 (foreground) and the queuefile is missing, then need
          to write it.  if queueName is set, use that, if not

          if you set the queuename, it might have variable values that when evaluated repeatedly (such as randomized settings)
          will come out differently every time. So even in the case of a fixed queue name, need to write 

        """

        if hasattr(self,'no') and self.no > 1:
            # worker instances need give lead instance time to write the queuefile
            time.sleep(randint(4,14))

            queue_file_read=False
            config_read_try=0
            while not queue_file_read:
                if os.path.isfile(queuefile):
                    f = open(queuefile, 'r')
                    self.queueName = f.read()
                    f.close()
                else:
                    self.queueName = ''

                config_read_try += 1
                logger.debug( f'instance read try {config_read_try} queueName {self.queueName} from queue state file {queuefile}' )
                if len(self.queueName) < 1:
                      nap=randint(1,4)
                      logger.debug( f'queue name corrupt take a short {nap} second nap, then try again' )
                      time.sleep(nap)
                      if config_read_try > 5:
                          logger.critical( f'failed to read queue name from {queuefile}')
                          sys.exit(2)
                else:
                      queue_file_read=True

        else: 
            # only lead instance (0-foreground, 1-start, or none in the case of 'declare')
            # should write the state file.

    
            # lead instance shou
            if os.path.isfile(queuefile):
                f = open(queuefile, 'r')
                self.queueName = f.read()
                f.close()
            
            #if the queuefile is corrupt, then will need to guess anyways.
            if ( self.queueName is None ) or ( self.queueName == '' ):
                queueShare = self._varsub(self.queueShare)
                self.queueName = f"q_{self.broker.url.username}." + '.'.join([component,cfg,queueShare])
                logger.debug( f'default guessed queueName  {self.queueName} ' )
    
            if self.action not in [ 'start', 'foreground', 'declare' ]:
                return

            # first make sure directory exists.
            if not os.path.isdir(os.path.dirname(queuefile)):
                pathlib.Path(os.path.dirname(queuefile)).mkdir(parents=True, exist_ok=True)

            if not os.path.isfile(queuefile) and (self.queueName is not None): 
                tmpQfile=queuefile+'.tmp'
                if not os.path.isfile(tmpQfile): 
                    f = open(tmpQfile, 'w')
                    f.write(self.queueName)
                    f.close()
                    os.rename( tmpQfile, queuefile )
                else:
                    logger.info( f'Queue name {self.queueName} being persisted to {queuefile} by some other process, so ignoring it.' )
                    return

                logger.debug( f'queue name {self.queueName} persisted to {queuefile}' )





    def finalize(self, component=None, config=None):
        """ 
         Before final use, take the existing settings, and infer any missing needed defaults from what is provided.
         Should be called prior to using a configuration.

         There are default options that apply only if they are not overridden... 
       """

        self._parse_sum(None)

        if not component and self.component:
            component = self.component
            
        if not config and self.config:
            config = self.config
            
        if self.action not in self.actions:
            logger.error( f"invalid action: {self.action} must be one of: {','.join(self.actions)}" )

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

        if self.directory:
            self.directory = os.path.expanduser(self.directory)

        # double check to ensure duration options are properly parsed
        for d in duration_options:
            if hasattr(self, d) and (type(getattr(self, d)) is str):
                setattr(self, d, durationToSeconds(getattr(self, d)))

        if hasattr(self, 'kbytes_ps'):
            bytes_ps = parse_count(self.kbytes_ps)
            if not self.kbytes_ps[-1].isalpha():
                bytes_ps *= 1024
            setattr(self, 'byteRateMax', bytes_ps)

        for d in count_options:
            if hasattr(self, d) and (type(getattr(self, d)) is str):
                setattr(self, d, parse_count(getattr(self, d)))

        for d in size_options:
            if hasattr(self, d) and (type(getattr(self, d)) is str):
                setattr(self, d, chunksize_from_str(getattr(self, d)))

        for f in flag_options:
            if hasattr(self, f) and (type(getattr(self, f)) is str):
                setattr(self, f, isTrue(getattr(self, f)))

        for f in float_options:
            if hasattr(self, f) and (type(getattr(self, f)) is str):
                setattr(self, f, parse_float(getattr(self, f)))

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
                delattr( self, 'nodupe_basis' )
            elif self.nodupe_basis == 'name': 
                self.plugins_early.append( 'nodupe.name' )
                delattr( self, 'nodupe_basis' )

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

        # FIXME: note that v2 *user_cache_dir* is, v3 called:  cfg_run_dir
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

            if hasattr(self,'post_exchange') and (type(self.post_exchange) is list ):
                pass
            elif hasattr(self, 'post_exchangeSplit') and self.post_exchangeSplit > 1:
                l = []
                for i in range(0, int(self.post_exchangeSplit)):
                    y = self.post_exchange + '%02d' % i
                    l.append(y)
                self.post_exchange = l
            else:
                self.post_exchange = [self.post_exchange]

            if (component in ['poll' ]) and (hasattr(self,'vip') and self.vip):
                if (not hasattr(self,'exchange') or not self.exchange):
                    if type(self.post_exchange) is list:
                        self.exchange = self.post_exchange[0]
                    else:
                        self.exchange = self.post_exchange
                if (not hasattr(self,'broker') or not self.broker):
                    self.broker = self.post_broker

        if not ( hasattr(self, 'source') or self.sourceFromExchange):
            if hasattr(self, 'post_broker') and hasattr(self.post_broker,'url') and self.post_broker.url.username:
               self.source = self.post_broker.url.username
            elif hasattr(self, 'broker') and hasattr(self.broker,'url') and self.broker.url.username:
               self.source = self.broker.url.username

        if self.broker and self.broker.url and self.broker.url.username:
            self._resolve_exchange()
            self._resolveQueueName(component,cfg)

        valid_inlineEncodings = [ 'guess', 'text', 'binary' ]
        if hasattr(self, 'inlineEncoding') and self.inlineEncoding not in valid_inlineEncodings:
            logger.error( f"{component}/{config} invalid inlineEncoding: {self.inlineEncoding} must be one of: {','.join(valid_inlineEncodings)}" )

        if hasattr(self, 'no'):
            if self.statehost:
                hostdir = self.hostdir
            else:
                hostdir = None
            self.metricsFilename = get_metrics_filename(hostdir, component, cfg, self.no)
            self.pid_filename = get_pid_filename(hostdir, component, cfg, self.no)
            self.retry_path = self.pid_filename.replace('.pid', '.retry')
            self.novipFilename = self.pid_filename.replace('.pid', '.noVip')


        if (self.bindings == [] and hasattr(self, 'exchange')):
            self.bindings = [(self.exchange, self.topicPrefix, [ '#' ])]

        if hasattr(self, 'documentRoot') and (self.documentRoot is not None):
            path = os.path.expanduser(os.path.abspath(self.documentRoot))
            if self.realpathPost:
                path = os.path.realpath(path)

            if sys.platform == 'win32' and words0.find('\\'):
                logger.warning("{component}/{config} %s %s" % (words0, words1))
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
                logger.debug( f"{component}/{config} defaulting post_baseUrl to match pollURl, since it isn't specified." )
                self.post_baseUrl = self.pollUrl
            
        # verify post_baseDir

        if self.post_baseDir is None:
            if self.post_documentRoot is not None:
                self.post_baseDir = os.path.expanduser(self.post_documentRoot)
                logger.warning("use post_baseDir instead of post_documentRoot")
            elif self.documentRoot is not None:
                self.post_baseDir = os.path.expanduser(self.documentRoot)
                logger.warning("use post_baseDir instead of documentRoot")
            elif self.post_baseUrl and ( self.post_baseUrl[0:5] in [ 'file:' ] ):
                self.post_baseDir = self.post_baseUrl[5:]
            elif self.post_baseUrl and ( self.post_baseUrl[0:5] in [ 'sftp:' ] ):
                u =  sarracenia.baseUrlParse(self.post_baseUrl) 
                self.post_baseDir = u.path
            elif self.baseDir is not None:
                self.post_baseDir = os.path.expanduser(self.baseDir)
                logger.debug("{component}/{config} defaulting post_baseDir to same as baseDir")


        if self.messageCountMax > 0:
            if self.batch > self.messageCountMax:
                self.batch = self.messageCountMax
                logger.info( f'{component}/{config} overriding batch for consistency with messageCountMax: {self.batch}' )

        if (component not in ['poll' ]):
            self.path = list(map( os.path.expanduser, self.path ))
        else:
            if not (hasattr(self,'scheduled_interval') or hasattr(self,'scheduled_hour') or hasattr(self,'scheduled_minute') or hasattr(self,'scheduled_time')):
                if self.sleep > 1:
                    self.scheduled_interval = self.sleep
                    self.sleep=1

        if self.runStateThreshold_hung < self.housekeeping:
            logger.warning( f"{component}/{config} runStateThreshold_hung {self.runStateThreshold_hung} set lower than housekeeping {self.housekeeping}. sr3 sanity might think this flow is hung and kill it too quickly.")

        if self.vip and not features['vip']['present']:
            logger.critical( f"{component}/{config} vip feature requested, but missing library: {' '.join(features['vip']['modules_needed'])} " )
            sys.exit(1)

    def check_undeclared_options(self):

        alloptions = str_options + flag_options + float_options + list_options + set_options + count_options + size_options + duration_options
        # FIXME: confused about this...  commenting out for now...
        for f,l,u in self.undeclared:
            if u not in alloptions:
                logger.error( f"{f}:{l} undeclared option: {u}")
            elif u in flag_options:
                if type( getattr(self,u) ) is not bool:
                    setattr(self,u,isTrue(getattr(self,u)))
            elif u in float_options:
                if type( getattr(self,u) ) is not float:
                    setattr(self,u,parse_float(getattr(self,u)))
            elif u in set_options:
                if type( getattr(self,u) ) is not set:
                    setattr(self,u,self._parse_set_string(getattr(self,u),set()))
            elif u in str_options:
                if type( getattr(self,u) ) is not str:
                    setattr(self,u,str(getattr(self,u)))
            elif u in count_options:
                if type( getattr(self,u) ) not in [ int, float ]:
                    setattr(self,u,parse_count(getattr(self,u)))
            elif u in size_options:
                if type( getattr(self,u) ) not in [ int, float ]:
                    setattr(self,u,parse_count(getattr(self,u)))
            elif u in duration_options:
                if type( getattr(self,u) ) not in [ int, float ]:
                    setattr(self,u,durationToSeconds(getattr(self,u)))
            # list options are the default, so no need to regularize

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

    def variableExpansion(self, cdir, message=None ) -> str:
        """
            replace substitution patterns, variable substitutions as described in
            https://metpx.github.io/sarracenia/Reference/sr3_options.7.html#variables

            returns:  the given string with the substiturions done.

            examples:   ${YYYYMMDD-70m} becomes 20221107 assuming that was the current date 70 minutes ago.
                        environment variables, and built-in settings are replaced also.

           timeoffset -70m


        """

        if not '$' in cdir:
            return cdir

        new_dir = cdir

        while '${BD}' in new_dir and self.baseDir != None:
            new_dir = new_dir.replace('${BD}', self.baseDir, 1)

        while ( '${BUP}' in new_dir ) and ( 'baseUrl' in message ):
            u = sarracenia.baseUrlParse( message['baseUrl'] )
            new_dir = new_dir.replace('${BUP}', u.path, 1 )

        while ( '${baseUrlPath}' in new_dir ) and ( 'baseUrl' in message ):
            u = sarracenia.baseUrlParse( message['baseUrl'] )
            new_dir = new_dir.replace('${baseUrlPath}', u.path, 1)

        while ( '${BUPL}' in new_dir ) and ( 'baseUrl' in message ):
            u = sarracenia.baseUrlParse( message['baseUrl'] )
            new_dir = new_dir.replace('${BUPL}', os.path.basename(u.path), 1 )

        while ( '${baseUrlPathLast}' in new_dir )  and ( 'baseUrl' in message ):
            u = sarracenia.baseUrlParse( message['baseUrl'] )
            new_dir = new_dir.replace('${baseUrlPathLast}', os.path.basename(u.path), 1 )

        while '${PBD}' in new_dir and self.post_baseDir != None:
            new_dir = new_dir.replace('${PBD}', self.post_baseDir, 1)

        while '${DR}' in new_dir and self.documentRoot != None:
            logger.warning(
                "DR = documentRoot should be replaced by BD for base_dir")
            new_dir = new_dir.replace('${DR}', self.documentRoot, 1)

        while '${PDR}' in new_dir and self.post_baseDir != None:
            logger.warning(
                "PDR = post_documentRoot should be replaced by PBD for post_baseDir"
            )
            new_dir = new_dir.replace('${PDR}', self.post_baseDir, 1)

        #whenStamp = time.gmtime( time.time()+self.varTimeOffset )

        whenStamp = datetime.datetime.fromtimestamp( time.time()+self.varTimeOffset )

        while '${YYYYMMDD}' in new_dir:
            YYYYMMDD = whenStamp.strftime("%Y%m%d")
            new_dir = new_dir.replace('${YYYYMMDD}', YYYYMMDD)

        while '${SOURCE}' in new_dir:
            new_dir = new_dir.replace('${SOURCE}', message['source'])

        while '${DD}' in new_dir:
            DD = whenStamp.strftime("%d")
            new_dir = new_dir.replace('${DD}', DD)

        while '${HH}' in new_dir:
            HH = whenStamp.strftime("%H")
            new_dir = new_dir.replace('${HH}', HH)

        while '${YYYY}' in new_dir:
            YYYY = whenStamp.strftime("%Y")
            new_dir = new_dir.replace('${YYYY}', YYYY)

        while '${MM}' in new_dir:
            MM = whenStamp.strftime("%m")
            new_dir = new_dir.replace('${MM}', MM)

        while '${JJJ}' in new_dir:
            JJJ = whenStamp.strftime("%j")
            new_dir = new_dir.replace('${JJJ}', JJJ)


        # strftime compatible patterns.
        fragments = new_dir.split( '${%' )
        if len(fragments) > 1:
            fragment_list=[fragments[0]]
            for fragment in fragments[1:]:
                close_brace = fragment.find('}')
                frag_start=0
                seconds=self.varTimeOffset

                # only support %o time offsets at the beginning of the string.
                if fragment[0] in [ '+', '-', 'o'  ]:
                    end_of_offset=fragment.find('%')
                    if fragment[0] == 'o':
                        s= 2 if fragment[1] in [ '-','+' ] else 1
                    else:
                        s= 1 if fragment[0] in [ '-','+' ] else 0
                    seconds = durationToSeconds(fragment[s:end_of_offset])
                    frag_start=end_of_offset+1
                    if '-' in fragment[0:2]: 
                        seconds = -1 * seconds

                whenStamp = datetime.datetime.fromtimestamp( time.time()+seconds )
        
                if close_brace > 0:
                    time_str=whenStamp.strftime( "%"+fragment[frag_start:close_brace] )
                    fragment_list.append(time_str)
                    fragment_list.append(fragment[close_brace+1:])
                else:
                    fragment_list.append(fragment)
            new_dir=''.join(fragment_list)
        
        # Parsing cdir to subtract time from it in the following formats
        # time unit can be: sec/mins/hours/days/weeks

        # ${YYYY-[number][time_unit]}
        offset_check = re.search( r'\$\{YYYY-(\d+)(\D)\}', cdir)
        if offset_check:
            logger.info( f"offset 0: {offset_check.group(1,2)}" )
            seconds = durationToSeconds(''.join(offset_check.group(1, 2)),
                                             's')

            epoch = time.mktime(time.gmtime()) - seconds
            YYYY1D = time.strftime("%Y", time.localtime(epoch))
            new_dir = re.sub( r'\$\{YYYY-\d+\D\}', YYYY1D, new_dir)

        # ${MM-[number][time_unit]}
        offset_check = re.search( r'\$\{MM-(\d+)(\D)\}', cdir)
        if offset_check:
            logger.info( f"offset 1: {offset_check.group(1,2)}" )
            seconds = durationToSeconds(''.join(offset_check.group(1, 2)),
                                             's')

            epoch = time.mktime(time.gmtime()) - seconds
            MM1D = time.strftime("%m", time.localtime(epoch))
            new_dir = re.sub( r'\$\{MM-\d+\D\}', MM1D, new_dir)

        # ${JJJ-[number][time_unit]}
        offset_check = re.search(r'\$\{JJJ-(\d+)(\D)\}', cdir)
        if offset_check:
            logger.info( f"offset 2: {offset_check.group(1,2)}" )
            seconds = durationToSeconds(''.join(offset_check.group(1, 2)),
                                             's')

            epoch = time.mktime(time.gmtime()) - seconds
            JJJ1D = time.strftime("%j", time.localtime(epoch))
            new_dir = re.sub( r'\$\{JJJ-\d+\D\}', JJJ1D, new_dir)

        # ${YYYYMMDD-[number][time_unit]}
        offset_check = re.search(r'\$\{YYYYMMDD-(\d+)(\D)\}', cdir)
        if offset_check:
            logger.info( f"offset 3: {offset_check.group(1,2)}" )
            seconds = durationToSeconds(''.join(offset_check.group(1, 2)),
                                             's')
            epoch = time.mktime(time.gmtime()) - seconds
            YYYYMMDD = time.strftime("%Y%m%d", time.localtime(epoch))
            logger.info( f"seconds: {seconds} YYYYMMDD {YYYYMMDD}" )
            new_dir = re.sub( r'\$\{YYYYMMDD-\d+\D\}', YYYYMMDD, new_dir)

        new_dir = self._varsub(new_dir)

        # substitute positional fields from the regex accept (0,1,2,3...)
        if message and '_matches' in message and len(new_dir.split( '${' )) > 1:
            fragment_list=[]
            for fragment in new_dir.split( '${' ):
                close_brace = fragment.find('}')
                frag_start=0
                if close_brace < 0 :
                    fragment_list.append(fragment)
                    continue

                match_field=fragment[0:close_brace]
                matches= re.search( r'^[0-9]+$', match_field)
                # non-numeric thing... variable or something.
                if not matches:
                    fragment_list.append('${' + fragment)
                    continue
                field=int(match_field)
                if self.sundew_compat_regex_first_match_is_zero:
                    field +=1
                if len(message['_matches'].groups()) >= field:
                    fragment_list.append(message['_matches'].group(field))
                    fragment_list.append(fragment[close_brace+1:])
                else:
                    logger.error( f"only {len(message['_matches'].groups())} groups in regex, group number too high: ${{{fragment}" )
                    fragment_list.append('${' +fragment)

            new_dir=''.join(fragment_list)

            #del message['_matches']
            #message['_deleteOnPost'] -= set(['_matches'])
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
           accept a configuration, apply argParse library to augment the given configuration
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
            '--blockSize',
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
                            type=int,
                            default=0,
                            help='Confirm you want to do something dangerous')
        parser.add_argument('--debug',
                            action='store_true',
                            default=self.debug,
                            help='print debugging output (very verbose)')
        parser.add_argument('--wololo',
                            action='store_true',
                            default=self.wololo,
                            help='force overwrite of converted configs')
        parser.add_argument('--dry_run', '--simulate', '--simulation', 
                            action='store_true',
                            default=self.dry_run,
                            help='simulation mode (perform no file transfers, just print what would happen)')
        parser.add_argument('--exchange',
                            nargs='?',
                            default=self.exchange,
                            help='root of the topic tree to subscribe to')

        parser.add_argument('--full',
                            action='store_true',
                            default=self.displayFull,
                            help='fuller, more verbose display')
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

        parser.add_argument('--identity_method', '--identity', '-s', '--sum',
                            nargs='?',
                            default=self.identity_method,
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
        parser.add_argument('--retry_refilter',
                            action='store_true',
                            default=self.retry_refilter,
                            help='repeat message processing when retrying transfers (default just resends as previous attempt.)')
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

        if hasattr(args,'full'):
            self.displayFull = args.full
            delattr(args,'full')

        self.merge(args)


def default_config():

    cfg = Config()
    cfg.currentDir = None
    cfg.override(default_options)
    cfg.override(sarracenia.moth.default_options)
    if features['amqp']['present']:
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
    if features['amqp']['present']:
        cfg.override(sarracenia.moth.amqp.default_options)
    cfg.override(sarracenia.flow.default_options)
    cfg.cfg_run_dir = '.'
    cfg.retry_path = '.'
    return cfg


def one_config(component, config, action, isPost=False):
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
        fname = os.path.expanduser(config + '.conf')
    else:
        fname = os.path.expanduser(config)

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

    cfg.action=action

    cfg.finalize(component, config)

    if component in ['post', 'watch']:
        cfg.postpath = list( map( os.path.expanduser, cfg.configurations[1:]))
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


    if cfg_preparse.logRotateInterval < 24*24*60:
        logRotateInterval=int(cfg_preparse.logRotateInterval)
        lr_when='s'
    else:
        logRotateInterval = int(cfg_preparse.logRotateInterval/(24*24*60))
        lr_when='midnight'

    # init logs here. need to know instance number and configuration and component before here.

    if cfg_preparse.action == 'start' and not cfg_preparse.logStdout:
        if cfg_preparse.statehost:
            hostdir = cfg_preparse.hostdir
        else:
            hostdir = None

        metricsfilename = get_metrics_filename( hostdir, component, config, child_inst)

        dir_not_there = not os.path.exists(os.path.dirname(metricsfilename))
        while dir_not_there:
            try:
                os.makedirs(os.path.dirname(metricsfilename), exist_ok=True)
                dir_not_there = False
            except FileExistsError:
                dir_not_there = False
            except Exception as ex:
                logging.error( "makedirs {} failed err={}".format(os.path.dirname(metricsfilename),ex))
                logging.debug("Exception details:", exc_info=True)
                time.sleep(0.1)

        cfg_preparse.metricsFilename = metricsfilename

        logfilename = get_log_filename( hostdir, component, config, child_inst)

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
                time.sleep(0.1)

        #log_format = '%(asctime)s [%(levelname)s] %(name)s %(funcName)s %(message)s'
        log_format = cfg_preparse.logFormat
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
            backupCount=cfg_preparse.logRotateCount)
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
