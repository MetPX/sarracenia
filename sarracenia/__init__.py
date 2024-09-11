#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
#
########################################################################
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; version 2 of the License.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
#
#
from ._version import __version__


from base64 import b64decode, b64encode
import calendar
import datetime
import humanize
import importlib.util
import io
import logging
import os
import os.path
import random
import re
from sarracenia.featuredetection import features
import stat as os_stat
import sys
import time
import types
import urllib
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

def baseUrlParse( url ):
    upr = urllib.parse.urlparse(url)
    u = types.SimpleNamespace()
    u.scheme = upr.scheme
    u.netlog = upr.netloc
    u.params = upr.params
    u.query = upr.query
    u.fragment = upr.fragment
    u.path = upr.path
    if u.scheme in [ 'sftp', 'file' ]:
        while u.path.startswith('//'):
            u.path = u.path[1:]
    return u


if features['filetypes']['present']:
   import magic

if features['mqtt']['present']:
   import paho.mqtt.client
   if not hasattr( paho.mqtt.client, 'MQTTv5' ):
       # without v5 support, mqtt is not useful.
       features['mqtt']['present'] = False

# if humanize is not present, compensate...
if features['humanize']['present']:
    import humanize

    def naturalSize( num ):
        return humanize.naturalsize(num,binary=True).replace(" ","")

    def naturalTime( dur ):
        return humanize.naturaltime(dur)

else:
  
    def naturalSize( num ):
       return "%g" % num

    def naturalTime( dur ):
       return "%g" % dur


if features['appdirs']['present']:
    import appdirs

    def site_config_dir( app, author ):
        return appdirs.site_config_dir( app, author )

    def user_config_dir( app, author ):
        return appdirs.user_config_dir( app, author )

    def user_cache_dir( app, author ):
        return appdirs.user_cache_dir( app, author )
else:
    # if appdirs is missing, pretend we're on Linux.
    import pathlib

    def site_config_dir( app, author ):
        return '/etc/xdg/xdg-ubuntu-xorg/%s' % app

    def user_config_dir( app, author ):
        return str(pathlib.Path.home()) + '/.config/%s' % app
 
    def user_cache_dir( app, author ):
        return str(pathlib.Path.home()) + '/.cache/%s' % app

"""
 end of extra feature scan. 

"""

import sarracenia.filemetadata

class Sarracenia:
    """
        Core utilities of Sarracenia. The main class here is sarracenia.Message.
        a Sarracenia.Message is subclassed from a dict, so for most uses, it works like the 
        python built-in, but also we have a few major entry points some factoryies:
    

        **Building a message from a file**

        m = sarracenia.Message.fromFileData( path, options, lstat )
     
        builds a notification message from a given existing file, consulting *options*, a parsed
        in memory version of the configuration settings that are applicable

        **Options**

        see the sarracenia.config.Config class for functions to parse configuration files
        and create corresponding python option dictionaries. One can supply small 
        dictionaries for example::

          options['topicPrefix'] = [ 'v02', 'post' ]
          options['bindings'] = [ ('xpublic', [ 'v02', 'post'] , [ '#' ] )]
          options['queueName'] = 'q_anonymous_' + socket.getfqdn() + '_SomethingHelpfulToYou'

        Above is an example of a minimal options dictionary taken from the tutorial 
        example called moth_api_consumer.py. often 
        

        **If you don't have a file**

        If you don't have a local file, then build your notification message with:
    
        m = sarracenia.Message.fromFileInfo( path, options, lstat )
    
        where you can make up the lstat values to fill in some fields in the message.
        You can make a fake lstat structure to provide these values using sarracenia.filemetadata
        class which is either an alias for paramiko.SFTPAttributes 
        ( https://docs.paramiko.org/en/latest/api/sftp.html#paramiko.sftp_attr.SFTPAttributes )
        if paramiko is installed, or a simple emulation if not.
    
    
        from  sarracenia.filemetadata import FmdStat
    
        lstat = FmdStat()
        lstat.st_mtime= utcinteger second count in UTC (numeric version of a Sarracenia timestamp.)
        lstat.st_atime=
        lstat.st_mode=0o644
        lstat.st_size= size_in_bytes
    
        optional fields that may be of interest:
        lstat.filename= "nameOfTheFile"
        lstat.longname= 'lrwxrwxrwx    1 peter    peter          20 Oct 11 20:28 nameOfTheFile'
     
        that you can then provide as an *lstat* argument to the above *fromFileInfo()* 
        call. However the notification message returned will lack an identity checksum field.
        once you get the file, you can add the Identity field with:
    
        m.computeIdentity(path, o):
    
        In terms of consuming notification messages, the fields in the dictionary provide metadata
        for the announced resource. The anounced data could be embedded in the notification message itself,
        or available by a URL.
    
        Messages are generally gathered from a source such as the Message Queueing Protocol wrapper
        class: moth... sarracenia.moth. 
    
    
        data = m.getContent()
    
        will return the content of the announced resource as raw data.
    
    """
    pass


class TimeConversions:
    """
    
     Time conversion routines.  

     * os.stat, and time.now() return floating point 

     * The floating point representation is a count of seconds since the beginning of the epoch.

     * beginning of epoch is platform dependent, and conversion to actual date is fraught (leap seconds, etc...)

     * Entire SR_* formats are text, no floats are sent over the protocol 
       (avoids byte order issues, null byte / encoding issues, and enhances readability.) 

     * str format: YYYYMMDDHHMMSS.msec goal of this representation is that a naive 
       conversion to floats yields comparable numbers.

     * but the number that results is not useful for anything else, so need these 
       special routines to get a proper epochal time.

     * also OK for year 2032 or whatever (rollover of time_t on 32 bits.)

     * string representation is forced to UTC timezone to avoid having to communicate timezone.
    
     timestr2flt() - accepts a string and returns a float.
    
     caveat

     FIXME: this encoding will break in the year 10000 (assumes four digit year) 
     and requires leading zeroes prior to 1000. One will have to add detection of 
     the decimal point, and change the offsets at that point.
        
    """
    pass


def stat( path ) -> sarracenia.filemetadata.FmdStat:
    """
       os.stat call replacement which improves on it by returning
       and SFTPAttributes structure, in place of the OS stat one,
       featuring:
 
       * mtime and ctime with subsecond accuracy 
       * fields that can be overridden (not immutable.)

    """
    native_stat = os.stat( path )
    
    sa = sarracenia.filemetadata.FmdStat()
    sa.st_mode = native_stat.st_mode
    sa.st_ino = native_stat.st_ino
    sa.st_dev  = native_stat.st_dev
    # st_nlink does not exist in paramiko.SFTPAttributes()
    #  FmdStat comes from that type.
    #sa.st_nlink  = native_stat.st_nlink
    sa.st_uid  = native_stat.st_uid
    sa.st_gid  = native_stat.st_gid
    sa.st_size  = native_stat.st_size

    sa.st_mtime = os.path.getmtime(path)
    sa.st_atime = os.path.getctime(path)
    sa.st_ctime = native_stat.st_atime
    return sa

def nowflt():
    return timestr2flt(nowstr())


def nowstr():
    return timeflt2str(time.time())


def timeflt2str(f=None):
    """
        timeflt2str - accepts a float and returns a string.

        flow is a floating point number such as returned by time.now()
        (number of seconds since beginning of epoch.)

        the str is YYYYMMDDTHHMMSS.sssss

        20210921T011331.0123

        translates to: Sept. 21st, 2021 at 01:13 and 31.0123 seconds.
        always UTC timezone.    
    """

    nsec = "{:.9g}".format(f % 1)[1:]
    return "{}{}".format(time.strftime("%Y%m%dT%H%M%S", time.gmtime(f)), nsec)


def timeValidate(s) -> bool:

    if len(s) < 14: return False
    if (len(s) > 14) and (s[8] != 'T') and (s[14] != '.'): return False
    if (len(s) > 15) and (s[8] == 'T') and (s[15] != '.'): return False
    if not s[0:8].isalnum(): return False
    return True


def timestr2flt(s):

    if s[8] == "T":
        s = s.replace('T', '')
    dt_tuple = int(s[0:4]), int(s[4:6]), int(s[6:8]), int(s[8:10]), int(
        s[10:12]), int(s[12:14])
    t = datetime.datetime(*dt_tuple, tzinfo=datetime.timezone.utc)
    return calendar.timegm(t.timetuple()) + float('0' + s[14:])


def timev2tov3str(s):
    if s[8] == 'T':
        return s
    else:
        return s[0:8] + 'T' + s[8:]

def durationToString(d) -> str:
    """
      given a numbner of seconds, return a short, human readable string.
    """
    if (d < 60):
        return f"{d:7.2f}s"

    first_part= humanize.naturaldelta(d).replace("minutes","m").replace("seconds","s").replace("hours","h").replace("days","d").replace("an hour","1h").replace("a day","1d").replace("a minute","1m").replace(" ","")

    second_part=""
    if first_part[-1] == 'm':
        rem=int(d-int(first_part[0:-1])*60)
        if rem > 0:
            second_part=f"{rem:d}s"
    if first_part[-1] == 'h':
        rem=int(( d-int(first_part[0:-1])*60*60 ) / 60 )
        if rem > 0:
            second_part=f"{rem:d}m"
    if first_part[-1] == 'd':
        rem=int (( d-int(first_part[0:-1])*60*60*24 ) / (60*60) )
        if rem > 0:
            second_part=f"{rem:d}h"
    return first_part+second_part 

def durationToSeconds(str_value, default=None) -> float:
    """
   this function converts duration to seconds.
   str_value should be a number followed by a unit [s,m,h,d,w] ex. 1w, 4d, 12h
   return 0.0 for invalid string.
   """
    factor = 1

    if type(str_value) in [list]:
        str_value = str_value[0]

    if type(str_value) in [int, float]:
        return str_value
    
    if type(str_value) is not str:
        return 0

    if str_value.lower() in [ 'none', 'off', 'false' ]:
        return 0

    if default and str_value.lower() in [ 'on', 'true' ]:
        return float(default)

    first_unit=None
    second_unit=str_value[-1].lower()
    if second_unit in 's': 
        factor *= 1
        first_unit='m'
    elif second_unit in 'm': 
        factor *= 60
        first_unit='h'
    elif second_unit in 'h': 
        factor *= 60 * 60
        first_unit='d'
    elif second_unit in 'd': 
        factor *= 60 * 60 * 24
        first_unit='w'
    elif second_unit in 'w': 
        factor *= 60 * 60 * 24 * 7

    if str_value[-1].isalpha(): str_value = str_value[:-1]

    if first_unit and first_unit in str_value: # two unit duration.
        (big, little) = str_value.split(first_unit)
        if big.isnumeric():
            big = int(big)
            if first_unit == 'm':
                 big = big*60
            elif first_unit == 'h':
                 big = big*60*60
            elif first_unit == 'd':
                 big = big*60*60*24
            elif first_unit == 'w':
                 big = big*60*60*24*7
            str_value = little
    else: 
        big=0

    try:
        duration = big + float(str_value) * factor
    except:
        logger.error( f"conversion failed for: +{str_value}+" )
        duration = 0.0

    return duration

"""
  report codes are cribbed from HTTP, when a new situation arises, just peruse a list,
  and pick one that fits. Should also be easier for others to use:

  https://en.wikipedia.org/wiki/List_of_HTTP_status_codes

"""
known_report_codes = {
    201: "Download successful. (variations: Downloaded, Inserted, Published, Copied, or Linked)",
    202: "Accepted. mkdir skipped as it already exists", 
    203: "Non-Authoritative Information: transformed during download.",
    205: "Reset Content: checksum recalculated on receipt.",
    206: "Partial Content: received and inserted.",
    304: "Not modified (Checksum validated, unchanged, so no download resulted.)",
    307: "Insertion deferred (writing to temporary part file for the moment.)",
    410: "Gone: server data different from notification message",
    417: "Expectation Failed: invalid notification message (corrupt headers)",
    422: "Unprocessable Content: could not determine path to transfer to",
    499: "Failure: Not Copied. SFTP/FTP/HTTP download problem",
    #FIXME : should  not have 503 error code 3 times in a row
    # 503: "Service unavailable. delete (File removal not currently supported.)",
    503: "Unable to process: Service unavailable",
    # 503: "Unsupported transport protocol specified in posting."
}


class Message(dict):
    """
        A notification message in Sarracenia is stored as a python dictionary, with a few extra management functions.

        The internal representation is very close to the v03 format defined here: https://metpx.github.io/sarracenia/Reference/sr_post.7.html

        Unfortunately, sub-classing of dict means that to copy it from a dict will mean losing the type,
        and hence the need for the copyDict member.
    """
    def __init__(self):
        self['_format'] = 'v03'
        self['_deleteOnPost'] = set(['_format'])


    def computeIdentity(msg, path, o, offset=0, data=None) -> None:
        """
           check extended attributes for a cached identity sum calculation.
           if extended attributes are present, and 
           * the file mtime is not too new, and 
           * the cached sum us using the same method
           then use the cached value.

           otherwise, calculate a checksum. 
           If the data is provided, use that as the file content, otherwise 
           read the file form the file system.  

           Once the checksum is determined,
           set the file's extended attributes for the new value.
           the method of checksum calculation is from options.identity.
           
           sets the message 'identity' field if appropriate.
        """
        xattr = sarracenia.filemetadata.FileMetadata(path)

        if not 'blocks' in msg:
            if o.randomize:
                methods = [
                    'random', 'md5', 'md5name', 'sha512', 'cod,md5', 'cod,sha512'
                ]
                calc_method = random.choice(methods)
            elif 'identity' in xattr.x and 'mtime' in xattr.x:
                if xattr.get('mtime') >= msg['mtime']:
                    logger.debug("mtime remembered by xattr")
                    fxainteg = xattr.get('identity')
                    if fxainteg['method'] == o.identity_method: 
                        msg['identity'] = fxainteg
                        return
                    logger.debug("xattr different method than on disk")
                    calc_method = o.identity_method
                else:
                    logger.debug("xattr sum too old")
                    calc_method = o.identity_method
            else:
                calc_method = o.identity_method
        else: 
            calc_method = o.identity_method

        if calc_method == None:
            return

        if 'mtime' in msg:
            xattr.set('mtime', msg['mtime'])

        logger.debug("mtime persisted, calc_method: {calc_method}")

        if calc_method[:4] == 'cod,' and len(calc_method) > 2:
            sumstr = calc_method
        elif calc_method in [ 'md5name', 'invalid' ]:
            xattr.persist()  # persist the mtime, at least...
            return  # no checksum needed for md5name. 
        elif calc_method == 'arbitrary':
            sumstr = {
                'method': 'arbitrary',
                'value': o.identity_arbitrary_value
            }
        else: # a "normal" calculation method, liks sha512, or md5
            sumalgo = sarracenia.identity.Identity.factory(calc_method)
            sumalgo.set_path(path)

            # compute checksum
            if calc_method in ['md5', 'sha512']:

                if data:
                    sumalgo.update(data)
                else:
                    fp = open(path, 'rb')
                    i = 0

                    #logger.info( f"offset: {offset}  size: {msg['size']} max: {offset+msg['size']} " )
                    if offset:
                        fp.seek( offset )

                    while i < offset+msg['size']:
                        buf = fp.read(o.bufSize)
                        if not buf: break
                        sumalgo.update(buf)
                        i += len(buf)
                    fp.close()

            # setting sumstr
            checksum = sumalgo.value
            sumstr = {'method': calc_method, 'value': checksum}

        msg['identity'] = sumstr
        xattr.set('identity', sumstr)
        xattr.persist()

    def copyDict(msg, d):
        """
          copy dictionary into message.
       """
        if d is None: return

        for h in d:
            msg[h] = d[h]

    def deriveSource(msg,o):
        """
           set msg['source'] field as appropriate for given message and options (o)
        """
        source=None
        if 'source' in o:
            source = o['source']
        elif 'sourceFromExchange' in o and o['sourceFromExchange'] and 'exchange' in msg:
            itisthere = re.match( "xs_([^_]+)_.*", msg['exchange'] )
            if itisthere:
                source = itisthere[1]
            else:
                itisthere = re.match( "xs_([^_]+)", msg['exchange'] )
                if itisthere:
                    source = itisthere[1]
        if 'source' in msg and 'sourceFromMessage' in o and o['sourceFromMessage']:
            pass
        elif source:
            msg['source'] = source
            msg['_deleteOnPost'] |= set(['source'])

    def deriveTopics(msg,o,topic,separator='.'):
        """
            derive subtopic, topicPrefix, and topic fields based on message and options.
        """
        msg_topic = topic.split(separator)
        # topic validation... deal with DMS topic scheme. https://github.com/MetPX/sarracenia/issues/1017
        if 'topicCopy' in o and o['topicCopy']:
            topicOverride=True
        else:
            topicOverride=False
            if 'relPath' in msg:
                path_topic = o['topicPrefix'] + os.path.dirname(msg['relPath']).split('/')

                if msg_topic != path_topic:
                    topicOverride=True

            # set subtopic if possible.
            if msg_topic[0:len(o['topicPrefix'])] == o['topicPrefix']:
                msg['subtopic'] = msg_topic[len(o['topicPrefix']):]
            else:
                topicOverride=True

        if topicOverride:
            msg['topic'] = topic
            msg['_deleteOnPost'] |= set( ['topic'] )


    def dumps(msg) -> str:
        """
           FIXME: used to be msg_dumps.
           print a message in a compact but relatively compact way.
           msg is a python dictionary. if there is a field longer than maximum_field_length, 
           truncate.
    
       """

        maximum_field_length = 255

        if msg is None: return ""

        if msg['_format'] == 'Wis':
            s = '{ '
            if 'id' in msg:
                s += f"{{ 'id': '{msg['id']}', 'type':'Feature', "
            if 'geometry' in msg:
                s += f"'geometry':{msg['geometry']} 'properties':{{ "
            else:
                s += "'geometry': None, 'properties':{ "

        else:
            s = "{ "

        for k in sorted(msg.keys()):

            if msg['_format'] == 'v04' and k in [ 'id', 'type', 'geometry' ]:
               continue
            
            if type(msg[k]) is dict:
                if k != 'properties':
                    v = "{ "
                for kk in sorted(msg[k].keys()):
                    v += " '%s':'%s'," % (kk, msg[k][kk])
                v = v[:-1] 
                if k != 'properties':
                   v += " }"
            else:
                try:
                    v = "%s" % msg[k]
                except:
                    v = "unprintable"

            if len(v) > maximum_field_length:
                v = v[0:maximum_field_length - 4] + '...'
                if v[0] == '{':
                    v += '}'

            s += f" '{k}':'{v}'," 

        if msg['_format'] == 'Wis':
            s += ' } '

        s = s[:-1] + " }"
        return s

    @staticmethod
    def fromFileData(path, o, lstat=None):
        """
            create a message based on a given file, calculating the checksum.
            returns a well-formed message, or none.
        """
        m = sarracenia.Message.fromFileInfo(path, o, lstat)
        if lstat :
            if os_stat.S_ISREG(lstat.st_mode):
                m.computeIdentity(path, o)
                if features['filetypes']['present']:
                    try:
                        t = magic.from_file(path,mime=True)
                        m['contentType'] = t
                    except Exception as ex:
                        logging.info("trying to determine mime-type. Exception details:", exc_info=True)
                #else:
                #    m['contentType'] = 'application/octet-stream' # https://www.rfc-editor.org/rfc/rfc2046.txt (default when clueless)
                # I think setting a bad value is worse than none, so just omitting.
            elif os_stat.S_ISDIR(lstat.st_mode):
                m['contentType'] = 'text/directory' # source: https://www.w3.org/2002/12/cal/rfc2425.html
            elif os_stat.S_ISLNK(lstat.st_mode):
                m['contentType'] = 'text/link' # I invented this one, could not find any reference
        return m

    @staticmethod
    def fromFileInfo(path, o, lstat=None):
        """
            based on the fiven information about the file (it's name and a stat record if available)
            and a configuration options object (sarracenia.config.Config) 
            return an sarracenia.Message suitable for placement on a worklist.

            A message is a specialized python dictionary with a certain set of fields in it.
            The message returned will have the necessary fields for processing and posting. 
    
            The message is built for a file is based on the given path, options (o), and lstat (output of os.stat)
             
            The lstat record is used to build 'atime', 'mtime' and 'mode' fields if 
            timeCopy and permCopy options are set.
    
            if no lstat record is supplied, then those fields will not be set.
        """

        msg = Message()

        #FIXME no variable substitution... o.variableExpansion ?
        if hasattr(o,'post_format') :
            msg['_format'] = o.post_format
        elif hasattr(o,'post_topicPrefix') and o.post_topicPrefix[0] in [ 'v02', 'v03' ]:
            msg['_format'] = o.post_topicPrefix[0]
        else:
            msg['_format'] = 'v03'

        if hasattr(o, 'post_exchange'):
            msg['exchange'] = o.post_exchange
        elif hasattr(o, 'exchange'):
            msg['exchange'] = o.exchange

        if hasattr(o, 'blockSize') and (o.blockSize > 1) and lstat and \
                (os_stat.S_IFMT(lstat.st_mode) == os_stat.S_IFREG) and \
                (lstat.st_size > o.blockSize):
           msg['blocks'] = { 'method': 'inplace', 'number':-1, 'size': o.blockSize, 'manifest': {}  }

        msg['local_offset'] = 0
        msg['_deleteOnPost'] = set(['exchange', 'local_offset', 'subtopic', '_format'])

        # notice
        msg['pubTime'] = timeflt2str(time.time())

        # set new_dir, new_file, new_subtopic, etc...
        msg.updatePaths(o, os.path.dirname(path), os.path.basename(path))

        # rename
        if 'new_relPath' in msg:
            post_relPath = msg['new_relPath']
        elif 'relPath' in msg:
            post_relPath = msg['relPath']
        else:
            post_relPath = None

        newname = post_relPath

        # rename path given with no filename

        if o.rename:
            msg['retrievePath'] = msg['new_retrievePath']
            newname = o.variableExpansion(o.rename)
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


        if o.identity_method:
            if o.identity_method.startswith('cod,'):
                msg['identity'] = {
                    'method': 'cod',
                    'value': o.identity_method[4:]
                }
            elif o.identity_method in ['random']:
                algo = sarracenia.identity.Identity.factory(o.identity_method)
                algo.set_path(post_relPath)
                msg['identity'] = {
                    'method': o.identity_method,
                    'value': algo.value
                }
        else:
            if 'identity' in msg:
                   del msg['identity']
 
        # for md5name/aka None aka omit identity... should just fall through.

        if lstat is None: return msg

        if (lstat.st_mode is not None) :
            msg['mode'] = "%o" % (lstat.st_mode & 0o7777)
            if not o.permCopy:
                msg['_deleteOnPost'] |= set(['mode'])
            
            if os_stat.S_ISDIR(lstat.st_mode):
                msg['fileOp'] = { 'directory': '' }
                return msg

        if lstat.st_size is not None:
            msg['size'] = lstat.st_size

        if lstat.st_mtime is not None:
            msg['mtime'] = timeflt2str(lstat.st_mtime)
        if lstat.st_atime is not None:
            msg['atime'] = timeflt2str(lstat.st_atime)

        if not o.timeCopy:
            msg['_deleteOnPost'] |= set([ 'atime', 'mtime' ])

        return msg

    @staticmethod
    def fromStream(path, o, data=None):
        """
           Create a file and message for the given path.  
           The file will be created or overwritten with the provided data.
           then invoke fromFileData() for the resulting file.
        """

        with open(path, 'wb') as fh:
            fh.write(data)

        if hasattr(o, 'chmod') and o.chmod:
            os.chmod(path, o.chmod)

        return sarracenia.Message.fromFileData(path, o, stat(path))

    def getIDStr(msg) -> str:
        """
           return some descriptive tag string to identify the message being processed.

        """
        s=""
        if 'baseUrl' in msg:
            s+=msg['baseUrl']+' '
        else:
            s+="baseUrl missing "
        if 'relPath' in msg and len(msg['relPath']) > 0:
            if msg['relPath'][0] != '/' and s and s[-1] != '/':
                s+='/'
            s+=msg['relPath']
        elif 'retrievePath' in msg and len(msg['retrievePath']) > 0 :
            if msg['retrievePath'][0] != '/' and s and s[-1] != '/':
                s+='/'
            s+= msg['retrievePath']
        else:
            s+='badMessage'
        return s


    def setReport(msg, code, text=None):
        """
          FIXME: used to be msg_set_report
          set message fields to indicate result of action so reports can be generated.
    
          set is supposed to indicate final message dispositions, so in the case
          of putting a message on worklist.failed... no report is generated, since
          it will be retried later.  FIXME: should we publish an interim failure report?
    
        """

        if code in known_report_codes:
            if text is None:
                text = known_report_codes[code]
                
        else:
            logger.warning('unknown report code supplied: %d:%s' %
                           (code, text))
            if text is None:
                text = 'unknown disposition'

        if 'report' in msg:
            logger.debug('overriding initial report: %d: %s' %
                           (msg['report']['code'], msg['report']['message']))

        msg['report'] = {'code': code, 'timeCompleted': nowstr(), 'message': text}
        msg['_deleteOnPost'] |= set(['report'])

    def updatePaths(msg, options, new_dir=None, new_file=None):
        """
        set the new_* fields in the message based on changed file placement.
        if new_* options are ommitted updaste the rest of the fields in 
        the message based on their current values.

        If you change file placement in a flow callback, for example.
        One would change new_dir and new_file in the message.
        This routines updates other fields in the message (e.g. relPath, 
        baseUrl, topic ) to match new_dir/new_file.

        msg['post_baseUrl'] defaults to msg['baseUrl']
     
        """

        # the headers option is an override.
        if hasattr(options, 'fixed_headers'):
            for k in options.fixed_headers:
                msg[k] = options.fixed_headers[k]

        msg['_deleteOnPost'] |= set([
            'new_dir', 'new_file', 'new_relPath', 'new_baseUrl', 'new_subtopic', 'subtopic', 'post_format'
        ])
        if new_dir:
            msg['new_dir'] = new_dir
        elif 'new_dir' in msg:
            new_dir = msg['new_dir']
        else:
            new_dir = ''

        if new_file or new_file == '':
            msg['new_file'] = new_file
        elif 'new_file' in msg:
            new_file = msg['new_file']
        elif 'new_relPath' in msg:
            new_file = os.path.basename(msg['new_relPath'])
        elif 'relPath' in msg:
            new_file = os.path.basename(msg['relPath'])
        else:
            new_file = 'ErrorInSarraceniaMessageUpdatePaths.txt'
    
        newFullPath = new_dir + '/' + new_file
        
        # post_baseUrl option set in msg overrides other possible options
        if 'post_baseUrl' in msg:
            baseUrl_str = msg['post_baseUrl']
        elif options.post_baseUrl:
            baseUrl_str = options.variableExpansion(options.post_baseUrl, msg)
        else:
            if 'baseUrl' in msg:
                baseUrl_str = msg['baseUrl']
            else:
                logger.error('missing post_baseUrl setting')
                return

        if options.post_format:
            msg['post_format'] = options.post_format
        elif options.post_topicPrefix:
            msg['post_format'] = options.post_topicPrefix[0]
        elif options.topicPrefix != msg['_format']:
            logger.warning( f"received message in {msg['_format']} format, expected {options.post_topicPrefix} " )
            msg['post_format'] = options.topicPrefix[0]
        else:
            msg['post_format'] = msg['_format']
           
        if hasattr(options, 'post_baseDir') and ( type(options.post_baseDir) is str ) \
            and ( len(options.post_baseDir) > 1):
            pbd_str = options.variableExpansion(options.post_baseDir, msg)
            parsed_baseUrl = sarracenia.baseUrlParse(baseUrl_str)

            if newFullPath.startswith(pbd_str):
                newFullPath = new_dir.replace(pbd_str, '', 1) + '/' + new_file

            if (len(parsed_baseUrl.path) > 1) and newFullPath.startswith(
                    parsed_baseUrl.path):
                newFullPath = newFullPath.replace(parsed_baseUrl.path, '', 1)

        if ('new_dir' not in msg) and options.post_baseDir:
            msg['new_dir'] = options.post_baseDir
            
        msg['new_baseUrl'] = baseUrl_str

        if len(newFullPath) > 0 and newFullPath[0] == '/':
            newFullPath = newFullPath[1:]

        msg['new_relPath'] = newFullPath
        msg['new_subtopic'] = newFullPath.split('/')[0:-1]

        for i in ['relPath', 'subtopic', 'baseUrl']:
            if not i in msg:
                msg[i] = msg['new_%s' % i]

        if sys.platform == 'win32':
            if 'new_dir' not in msg:
                msg['new_dir'] = msg['new_dir'].replace('\\', '/')
            msg['new_relPath'] = msg['new_relPath'].replace('\\', '/')
            if re.match('[A-Z]:', str(options.currentDir),
                        flags=re.IGNORECASE):
                msg['new_dir'] = msg['new_dir'].lstrip('/')
                msg['new_relPath'] = msg['new_relPath'].lstrip('/')

    def validate(msg):
        """
        FIXME: used to be msg_validate
        return True if message format seems ok, return True, else return False, log some reasons.
        """
        if not type(msg) is sarracenia.Message:
            logger.error( f"not a message")
            return False

        res = True
        for required_key in ['pubTime', 'baseUrl', 'relPath']:
            if not required_key in msg:
                logger.error( f'missing key: {required_key}' )
                res = False

        if not timeValidate(msg['pubTime']):
            logger.error( f"malformed pubTime: {msg['pubTime']}")
            res = False

        return res


    def getContent(msg,options=None):
        """
           Retrieve the data referred to by a message.  The data may be embedded
           in the messate, or this routine may resolve a link to an external server 
           and download the data.

           does not handle authentication.
           This routine is meant to be used with small files. using it to download
           large files may be very inefficient. Untested in that use-case.

           Return value is the data.

           often on server where one is publishing data, the file is available as
           a local file, and one can avoid the network usage by using a options.baseDir setting.
           this behaviour can be disabled by not providing the options or not setting baseDir.
        """

        # inlined/embedded case.
        if 'content' in msg:
            if msg['content']['encoding'] == 'base64':
                return b64decode(msg['content']['value'])
            else:
                return msg['content']['value'].encode('utf-8')

        path=''
        if msg['baseUrl'].startswith('file:'):
            pu = urllib.parse.urlparse(msg['baseUrl'])
            path=pu.path + msg['relPath']
            logger.info( f"path: {path}")
        elif options and hasattr(options,'baseDir') and options.baseDir:
            # local file shortcut
            path=options.baseDir + os.sep + msg['relPath']
        
        if os.path.exists(path):
            logger.info( f"reading local file path: {path} exists?: {os.path.exists(path)}" )
            with open(path,'rb') as f:
                return f.read()

        # case requiring resolution.
        if 'retrievePath' in msg:
            retUrl = msg['baseUrl'] + '/' + msg['retrievePath']
        else:
            retUrl = msg['baseUrl'] + '/' + msg['relPath']

        logger.info( f"retrieving from: {retUrl}" )
        with urllib.request.urlopen(retUrl) as response:
            return response.read()

    def new_pathWrite(msg,options,data):
        """
           expects: msg['new_dir'] and msg['new_file'] to be set.
           given the byte stream of data.

           write the local file based on the given message, options and data.  
           update the message to match same (recalculating checksum.)

           in future:
           If the data field is a file, then that is taken as an open file object
           which can be read sequentially, and the bytes write to the path indicated
           by other message fields.

           currently, if data is a buffer, then it's contents is written to the file.

           if data is None, then look for the 'content' header in the message.
           and use the data from that.

        """
        opath=msg['new_dir'] + os.sep + msg['new_file']

        if not os.path.isdir(msg['new_dir']):
            if self.o.permDirDefault != 0:
                os.makedirs(msg['new_dir'],mode=self.o.permDirDefault, exist_ok=True)
            else:
                os.makedirs(msg['new_dir'], exist_ok=True)

        # ide
        #if isinstance(data, io.IOBase ):
        #    with open(opath, 'wb') as f:
        #        while buf = data.read(self.o.bufSize) > 0 :
        #            sz=f.write(buf)

        if 'content' in msg:
            if data:
                del msg['content']
            elif msg['content']['encoding'] == 'base64':
                data=b64decode(msg['content']['value'])
            else:
                data=msg['content']['value'].encode('utf-8')
                
        try:
            with open(opath, 'wb') as f:
               sz=f.write(data)
            if self.o.permDefault != 0:
                os.chmod(opath,mode=self.o.permDefault)
            msg['size'] = sz
            msg.computeIdentity(opath,self.o,data=data)
        except Exception as ex:
            logger.error( f"problem with {opath}: {ex}" )
