#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
#
# __init__.py : contains version number of sarracenia
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
__version__ = "3.00.22"

from base64 import b64decode, b64encode
import calendar
import datetime
import importlib.util
import logging
import os
import os.path
import paramiko
import re
import sarracenia.filemetadata
import stat
import sys
import time
import urllib
import urllib.request

logger = logging.getLogger(__name__)


class Sarracenia:
    """
        Core utilities of Sarracenia.  The main class here is sarracenia.Message.
        a Sarracenia.Message is subclassed from a dict, so for most uses, it works like the 
        python built-in, but also we have a few major entry points some factoryies:
    

        **Building a message from a file**

        m = sarracenia.Message.fromFileData( path, options, lstat )
     
        builds a message from a given existing file, consulting *options*, a parsed
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

        If you don't have a local file, then build your message with:
    
        m = sarracenia.Message.fromFileInfo( path, options, lstat )
    
        where you can make up the lstat values to fill in some fields in the message.
        You can make a fake lstat structure to provide these values using paramiko.SFTPAttributes 
    
    
        import paramiko
    
        lstat = paramiko.SFTPAttributes()
        lstat.st_mtime= utcinteger second count in UTC (numeric version of a Sarracenia timestamp.)
        lstat.st_atime=
        lstat.st_mode=0o644
        lstat.st_size= size_in_bytes
    
        optional fields that may be of interest:
        lstat.filename= "nameOfTheFile"
        lstat.longname= 'lrwxrwxrwx    1 peter    peter          20 Oct 11 20:28 nameOfTheFile'
     
        that you can then provide as an *lstat* argument to the above *fromFileInfo()* 
        call. However the message returned will lack an integrity checksum field.
        once you get the file, you can add the Integrity field with:
    
        m.__computeIntegrity(path, o):
    
        In terms of consuming messages, the fields in the dictionary provide metadata
        for the announced resource. The anounced data could be embedded in the message itself,
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

     * Entire SR\_* formats are text, no floats are sent over the protocol 
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


def stat( path ) -> paramiko.SFTPAttributes:
    """
       os.stat call replacement which improves on it by returning
       and SFTPAttributes structure, in place of the OS stat one,
       featuring:
 
       * mtime and ctime with subsecond accuracy 
       * fields that can be overridden (not immutable.)

    """
    native_stat = os.stat( path )
    
    sa = paramiko.SFTPAttributes()
    sa.st_mode = native_stat.st_mode
    sa.st_ino = native_stat.st_ino
    sa.st_dev  = native_stat.st_dev 
    sa.st_nlink  = native_stat.st_nlink 
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

    if str_value.lower() in [ 'none', 'off', 'false' ]:
        return 0

    if default and str_value.lower() in [ 'on', 'true' ]:
        return float(default)

    if str_value[-1] in 'sS': factor *= 1
    elif str_value[-1] in 'mM': factor *= 60
    elif str_value[-1] in 'hH': factor *= 60 * 60
    elif str_value[-1] in 'dD': factor *= 60 * 60 * 24
    elif str_value[-1] in 'wW': factor *= 60 * 60 * 24 * 7
    if str_value[-1].isalpha(): str_value = str_value[:-1]

    try:
        duration = float(str_value) * factor
    except:
        logger.error("conversion failed for: %s" % str_value)
        duration = 0.0

    return duration


known_report_codes = {
    201:
    "Download successful. (variations: Downloaded, Inserted, Published, Copied, or Linked)",
    203: "Non-Authoritative Information: transformed during download.",
    205:
    "Reset Content: truncated. File is shorter than originally expected (changed length during transfer) This only arises during multi-part transfers.",
    205: "Reset Content: checksum recalculated on receipt.",
    304:
    "Not modified (Checksum validated, unchanged, so no download resulted.)",
    307: "Insertion deferred (writing to temporary part file for the moment.)",
    417: "Expectation Failed: invalid message (corrupt headers)",
    499: "Failure: Not Copied. SFTP/FTP/HTTP download problem",
    #FIXME : should  not have 503 error code 3 times in a row
    # 503: "Service unavailable. delete (File removal not currently supported.)",
    503: "Unable to process: Service unavailable",
    # 503: "Unsupported transport protocol specified in posting."
}


class Message(dict):
    """
        A message in Sarracenia is stored as a python dictionary, with a few extra management functions.

        unfortunately, sub-classing of dict means that to copy it from a dict will mean losing the type,
        and hence the need for the copyDict member.
    """
    def __computeIntegrity(msg, path, o):
        """
           check extended attributes for a cached integrity sum calculation.
           if extended attributes are present, and 
           * the file mtime is not too new, and 
           * the cached sum us using the same method
           then use the cached value.

           otherwise, calculate a checksum. 
           set the file's extended attributes for the new value.
           the method of checksum calculation is from options.integrity_method.
           
           sets the message 'integrity' field if appropriate.
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
                fxainteg = xattr.get('integrity')
                if fxainteg['method'] == o.integrity_method: 
                     msg['integrity'] = fxainteg
                     return
                logger.debug("xattr different method than on disk")
                calc_method = o.integrity_method
            else:
                logger.debug("xattr sum too old")
                calc_method = o.integrity_method
        else:
            calc_method = o.integrity_method

        logger.debug('FIXME calc_method: %s' % calc_method )
        if calc_method == None:
            return

        xattr.set('mtime', msg['mtime'])

        #logger.debug("sum set by compute_sumstr")

        if calc_method[:4] == 'cod,' and len(calc_method) > 2:
            sumstr = calc_method
        elif calc_method in [ 'md5name', 'invalid' ]:
            xattr.persist()  # persist the mtime, at least...
            return  # no checksum needed for md5name. 
        elif calc_method == 'arbitrary':
            sumstr = {
                'method': 'arbitrary',
                'value': o.integrity_arbitrary_value
            }
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
            checksum = sumalgo.value
            sumstr = {'method': calc_method, 'value': checksum}

        msg['integrity'] = sumstr
        xattr.set('integrity', sumstr)
        xattr.persist()

    def copyDict(msg, d):
        """
          copy dictionary into message.
       """
        if d is None: return

        for h in d:
            msg[h] = d[h]

    def dumps(msg) -> str:
        """
           FIXME: used to be msg_dumps.
           print a message in a compact but relatively compact way.
           msg is a python dictionary. if there is a field longer than maximum_field_length, 
           truncate.
    
       """

        maximum_field_length = 255

        if msg is None: return ""

        if msg['version'] == 'v04':
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

            if msg['version'] == 'v04' and k in [ 'id', 'type', 'geometry' ]:
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

        if msg['version'] == 'v04':
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
        m.__computeIntegrity(path, o)
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
        if hasattr(o,'post_topicPrefix') and o.post_topicPrefix[0] in [ 'v02', 'v03', 'v04' ]:
            msg['version'] = o.post_topicPrefix[0]
        else:
            msg['version'] = 'v03'

        if hasattr(o, 'post_exchange'):
            msg['exchange'] = o.post_exchange
        elif hasattr(o, 'exchange'):
            msg['exchange'] = o.exchange

        msg['local_offset'] = 0
        msg['_deleteOnPost'] = set(['exchange', 'local_offset', 'subtopic', 'version'])

        # notice
        msg['pubTime'] = timeflt2str(time.time())

        # set new_dir, new_file, new_subtopic, etc...
        msg.updatePaths(o, os.path.dirname(path), os.path.basename(path))

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

        if o.integrity_method:
            if o.integrity_method.startswith('cod,'):
                msg['integrity'] = {
                    'method': 'cod',
                    'value': o.integrity_method[4:]
                }
            elif o.integrity_method in ['random']:
                algo = sarracenia.integrity.Integrity.factory(o.integrity_method)
                algo.set_path(post_relPath)
                msg['integrity'] = {
                    'method': o.integrity_method,
                    'value': algo.value
                }
        else:
            if 'integrity' in msg:
                   del msg['integrity']
 
        # for md5name/aka None aka omit integrity... should just fall through.

        if lstat is None: return msg

        if lstat.st_size is not None:
            msg['size'] = lstat.st_size

        if o.timeCopy:
            if lstat.st_mtime is not None:
                msg['mtime'] = timeflt2str(lstat.st_mtime)
            if lstat.st_atime is not None:
                msg['atime'] = timeflt2str(lstat.st_atime)

        if (lstat.st_mode is not None) and  \
            (o.permCopy and lstat.st_mode):
            msg['mode'] = "%o" % (lstat.st_mode & 0o7777)

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
            logger.warning('overriding initial report: %d: %s' %
                           (msg['report']['code'], msg['report']['message']))

        msg['timeCompleted'] = nowstr()
        msg['report'] = {'code': code, 'message': text}
        msg['_deleteOnPost'] |= set(['report','timeCompleted'])

    def updatePaths(msg, options, new_dir, new_file):
        """
        set the new\_ fields in the message based on changed file placement.

        If you change file placement in a flow callback, for example.
        One would change new_dir and new_file in the message.
        This routines updates other fields in the message (e.g. relPath, 
        baseUrl, topic ) to match new_dir/new_file.

        msg['post_baseUrl'] defaults to msg['baseUrl']
     
        """

        msg['_deleteOnPost'] |= set([
            'new_dir', 'new_file', 'new_relPath', 'new_baseUrl', 'new_subtopic', 'post_version'
        ])
        msg['new_dir'] = new_dir
        msg['new_file'] = new_file

        relPath = new_dir + '/' + new_file

        if options.post_baseUrl:
            baseUrl_str = options.variableExpansion(options.post_baseUrl, msg)
        else:
            if 'baseUrl' in msg:
                baseUrl_str = msg['baseUrl']
            else:
                logger.error('missing post_baseUrl setting')
                return

        if options.post_topicPrefix:
            msg['post_version'] = options.post_topicPrefix[0]
        elif options.topicPrefix != msg['version']:
            logger.warning( f"received message in {msg['version']} format, expected {options.post_topicPrefix} " )
            msg['post_version'] = options.topicPrefix[0]
        else:
            msg['post_version'] = msg['version']
           
        if hasattr(options, 'post_baseDir') and ( type(options.post_baseDir) is str ) \
            and ( len(options.post_baseDir) > 1):
            pbd_str = options.variableExpansion(options.post_baseDir, msg)
            parsed_baseUrl = urllib.parse.urlparse(baseUrl_str)

            if relPath.startswith(pbd_str):
                relPath = new_dir.replace(pbd_str, '', 1) + '/' + new_file

            if (len(parsed_baseUrl.path) > 1) and relPath.startswith(
                    parsed_baseUrl.path):
                relPath = relPath.replace(parsed_baseUrl.path, '', 1)

        msg['new_baseUrl'] = baseUrl_str

        if relPath[0] == '/':
            relPath = relPath[1:]

        msg['new_relPath'] = relPath
        msg['new_subtopic'] = relPath.split('/')[0:-1]

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
            return False

        res = True
        for required_key in ['pubTime', 'baseUrl', 'relPath']:
            if not required_key in msg:
                logger.error('missing key: %s' % required_key)
                res = False

        if not timeValidate(msg['pubTime']):
            res = False

        if not res:
            logger.error('malformed message: %s', msg)
        return res

    def getContent(msg):
        """
           Retrieve the data referred to by a message.  The data may be embedded
           in the messate, or this routine may resolve a link to an external server 
           and download the data.

           does not handle authentication.
           This routine is meant to be used with small files. using it to download
           large files may be very inefficient. Untested in that use-case.

           Return value is the data.
        """

        # inlined/embedded case.
        if 'content' in msg:
            if msg['content']['encoding'] == 'base64':
                return b64decode(msg['content']['value'])
            else:
                return msg['content']['value'].encode('utf-8')
        # case requiring resolution.
        if 'retPath' in msg:
            retUrl = msg['baseUrl'] + '/' + msg['retPath']
        else:
            retUrl = msg['baseUrl'] + '/' + msg['relPath']

        with urllib.request.urlopen(retUrl) as response:
            return response.read()

"""
  Extra Feature Scanning and Enablement.

  checking for extra dependencies, not "hard" dependencies ("requires")
  listed as extras in setup.py and omitted entirely from debian packaging.
  this allows installation with fewer dependencies ahead of time, and then
  provide some messaging to users when they "need" an optional dependency.
 
  optional extras can be enabled using pip install metpx-sr3[extra]
  where extra is one of the features listed below. Alternatively,
  one can just install the modules that are needed and the functionality
  will be enabled after a component restart.
  
  amqp - ability to communicate with AMQP (rabbitmq) brokers
  mqtt - ability to communicate with MQTT brokers
  ftppoll - ability to poll FTP servers
  vip  - enable vip (Virtual IP) settings to implement singleton processing
         for high availability support.
  watch - monitor files or directories for changes.

"""
extras = { 
   'amqp' : { 'modules_needed': [ 'amqp' ], 'present': False, 'lament' : 'will not be able to connect to rabbitmq brokers' },
   'appdirs' : { 'modules_needed': [ 'appdirs' ], 'present': False, 'lament' : 'will assume linux file placement under home dir' },
   'ftppoll' : { 'modules_needed': ['dateparser', 'pytz'], 'present': False, 'lament' : 'will not be able to poll with ftp' },
   'humanize' : { 'modules_needed': ['humanize' ], 'present': False, 'lament': 'humans will have to read larger, uglier numbers' },
   'mqtt' : { 'modules_needed': ['paho.mqtt.client'], 'present': False, 'lament': 'will not be able to connect to mqtt brokers' },
   'vip'  : { 'modules_needed': ['netifaces'] , 'present': False, 'lament': 'will not be able to use the vip option for high availability clustering' },
   'watch'  : { 'modules_needed': ['watchdog'] , 'present': False, 'lament': 'cannot watch directories' }
}

for x in extras:
   
   extras[x]['present']=True
   for y in  extras[x]['modules_needed']:
       try:
           if importlib.util.find_spec( y ):
               #logger.debug( f'found feature {y}, enabled') 
               pass
           else:
               logger.debug( f"extra feature {x} needs missing module {y}. Disabled" ) 
               extras[x]['present']=False
       except:
           logger.debug( f"extra feature {x} needs missing module {y}. Disabled" ) 
           extras[x]['present']=False

# Some sort of graceful fallback, or good messaging for when dependencies are missing.

if extras['mqtt']['present']:
   import paho.mqtt.client
   if not hasattr( paho.mqtt.client, 'MQTTv5' ):
       # without v5 support, mqtt is not useful.
       extras['mqtt']['present'] = False

# if humanize is not present, compensate...
if extras['humanize']['present']:
    import humanize

    def naturalSize( num ):
        return humanize.naturalsize(num,binary=True)

    def naturalTime( dur ):
        return humanize.naturaltime(dur)

else:
  
    def naturalSize( num ):
       return "%g" % num

    def naturalTime( dur ):
       return "%g" % dur


if extras['appdirs']['present']:
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
 
