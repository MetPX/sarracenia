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
import logging
import stat
import time
from sarracenia import v3timeflt2str
import sarracenia.filemetadata

logger = logging.getLogger(__name__)


"""
  This file was originally a place holder... thought this was not needed, then there was a stack trace.
  and setup.py gets leaves the directory out if not present.

  then started finding this convenient for common routines.

"""

def msg_dumps(msg):
   """
       print a message in a compact but relatively compact way.
       msg is a python dictionary. if there is a field longer than maximum_field_length, 
       truncate.

   """

   maximum_field_length=255

   if msg is None: return ""

   s="{ "
   for k in sorted(msg.keys()):
      if type(msg[k]) is dict:
         v="{ " 
         for kk in sorted(msg[k].keys()):
            v+= " '%s':'%s'," % ( kk, msg[k][kk] )
         v=v[:-1]+" }"
      else:
         try:
             v="%s" % msg[k]
         except:
             v="unprintable"

      if len(v) > maximum_field_length: 
        v=v[0:maximum_field_length-4] + '...'
        if v[0] == '{':
          v += '}'

      s += " '%s':'%s'," % (k, v )

   s=s[:-1]+" }"
   return s

def msg_validate(msg):
    """
    return True if message format seems ok, return True, else return False, log some reasons.
    """
    if not type(msg) is dict:
        return False

    res=True
    for required_key in [ 'pubTime', 'baseUrl', 'relPath', 'integrity' ]:
        if not required_key in msg:
           logger.error('missing key: %s' % required_key )
           res=False
    if not res:
        logger.error('malformed message: %s', msg )
    return res

def msg_init(path, o, lstat=None):
    """
        return an message suitable for placement on a worklist.
        A message is a python dictionary with a certain set of fields in it.
        The message returned will have the necessary fields for processing and posting. 

        The message is built for a file is based on the given path, options (o), and lstat (output of os.stat)
         
        The lstat record is used to build 'atime', 'mtime' and 'mode' fields if 
        preserve_time and preserve_mode options are set.

        if no lstat record is supplied, then those fields will not be set.
    """

    msg = {}

    #FIXME no variable substitution... o.set_dir_pattern ?
 
    if hasattr(o,'post_exchange'):
        msg['exchange'] = o.post_exchange
    elif hasattr(o,'exchange'):
        msg['exchange'] = o.exchange

    msg['local_offset'] = 0
    msg['_deleteOnPost'] = set ( [ 'exchange', 'local_offset' ] )

    # notice
    msg['pubTime'] = v3timeflt2str(time.time())

    # set new_dir, new_file, new_subtopic, etc...
    o.set_newMessageUpdatePaths( msg, os.path.dirname(path), os.path.basename(path) )

    # rename
    post_relPath = msg['new_relPath']
    newname = post_relPath

    # rename path given with no filename

    if o.rename:
        newname = o.rename
        if o.rename[-1] == '/':
            newname += os.path.basename(path)

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

    msg['size'] = lstat.st_size

    if o.preserve_time:
        msg['mtime'] = v3timeflt2str(lstat.st_mtime)
        msg['atime'] = v3timeflt2str(lstat.st_atime)

    if o.preserve_mode:
        msg['mode'] = "%o" % (lstat.st_mode & 0o7777)

    return msg


def msg_computeIntegrity(path, o, msg):
        """
           check extended attributes for a cached integrity sum calculation.
           if present, and 
                  the file mtime is not too new, and 
                  the cached sum using the same method
              then use the cached value.

           otherwise, will need to use calculate a checksum.
           the method of checksum calculation is from options.integrity_method.
           
        """
        xattr = sarracenia.filemetadata.FileMetadata(path)

        if o.randomize:
            methods = [
                'random', 'md5', 'md5name', 'sha512', 'cod,md5', 'cod,sha512'
            ]
            calc_method = choice(methods)
        elif 'integrity' in xattr.x and 'mtime' in xattr.x:
            if xattr.get('mtime') >= msg['mtime']:
                logger.debug("mtime remembered by xattr")
                return xattr.get('integrity')
            else:
                logger.debug("xattr sum too old")
                calc_method = o.integrity_method
        else:
            calc_method = o.integrity_method

        xattr.set('mtime', msg['mtime'])

        #logger.debug("sum set by compute_sumstr")

        if calc_method[:4] == 'cod,' and len(calc_method) > 2:
            sumstr = calc_method
        else:
            sumalgo = sarracenia.integrity.Integrity.factory(calc_method)
            sumalgo.set_path(path)

            # compute checksum

            if calc_method in ['md5', 'sha512']:

                fp = open(path, 'rb')
                i = 0
                while i < msg['size']:
                    buf = fp.read(o.bufsize)
                    if not buf: break
                    sumalgo.update(buf)
                    i += len(buf)
                fp.close()

            # setting sumstr
            checksum = sumalgo.get_value()
            sumstr = {'method': calc_method, 'value': checksum}

        xattr.set('integrity', sumstr)
        xattr.persist()
        return sumstr

def msg_fromFile( path, o, lstat=None ):
    """
        create a message based on a given file.
        returns a well-formed message, or none.
    """
    m = msg_init( path, o, lstat )
    m['integrity'] = msg_computeIntegrity( path, o, m )
    return m


