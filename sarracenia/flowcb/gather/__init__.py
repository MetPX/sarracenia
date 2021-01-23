#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2020
#
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
#

import os.path
import stat
import time
from sarracenia import v3timeflt2str
"""
  This file was originally a place holder... thought this was not needed, then there was a stack trace.
  and setup.py gets leaves the directory out if not present.

  then started finding this convenient for common routines.

"""


def msg_init(path, o, lstat=None):

    msg = {}
    msg['new_dir'] = os.path.dirname(path)
    msg['new_file'] = os.path.basename(path)

    # relpath

    if o.post_baseDir:
        post_relPath = path.replace(o.post_baseDir, '')
    else:
        post_relPath = path

    # exchange
    msg['exchange'] = o.post_exchange

    # topic
    words = post_relPath.strip('/').split('/')
    if len(words) > 1:
        subtopic = '.'.join(words[:-1]).replace('..', '.')
    else:
        subtopic = ''
    msg['topic'] = o.post_topic_prefix + '.' + subtopic
    msg['local_offset'] = 0

    msg['_deleteOnPost'] = [
        'exchange', 'local_offset', 'new_dir', 'new_file', 'post_relpath'
    ]

    # notice
    msg['pubTime'] = v3timeflt2str(time.time())
    msg['relPath'] = post_relPath
    msg['baseUrl'] = o.post_baseUrl

    # rename
    newname = post_relPath

    # rename path given with no filename

    if o.rename:
        newname = o.rename
        if o.rename[-1] == '/':
            newname += os.path.basename(path)

    # following is a transcription of v2: path_rename

    # strip 'N' heading directories

    if o.strip > 0:
        strip = o.strip
        if path[0] == '/': strip = strip + 1
        # if we strip too much... keep the filename
        token = path.split('/')
        try:
            token = token[strip:]
        except:
            token = [os.path.basename(path)]
        newname = '/' + '/'.join(token)

    if newname != post_relPath: msg['rename'] = newname

    # headers

    if hasattr(o, 'to_clusters') and (o.to_clusters is not None):
        msg['to_clusters'] = o.to_clusters
    if hasattr(o, 'cluster') and (o.cluster is not None):
        msg['from_cluster'] = o.cluster

    if hasattr(o, 'source') and (o.source is not None):
        msg['source'] = o.source

    if hasattr(o, 'fixed_headers'):
        for k in o.fixed_headers:
            msg[k] = o.fixed_headers[k]

    if lstat is None: return msg

    if o.preserve_time:
        msg['mtime'] = v3timeflt2str(lstat.st_mtime)
        msg['atime'] = v3timeflt2str(lstat.st_atime)

    if o.preserve_mode:
        msg['mode'] = "%o" % (lstat[stat.ST_MODE] & 0o7777)

    return msg
