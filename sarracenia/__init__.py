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
__version__ = "3.00.013"

from base64 import b64decode, b64encode
import calendar
import datetime
import logging
import os
import os.path
import re
import sarracenia.filemetadata
import stat
import sys
import time
import urllib
import urllib.request

logger = logging.getLogger(__name__)

"""
    Core utilities of Sarracenia.  The main class here is sarracenia.Message.
    a Sarracenia.Message is subclassed from a dict, so for most uses, it works like the 
    python built-in, but also we have a few major entry points some factoryies:

    m = sarracenia.Message.fromFileData( path, options, lstat )
 
    which builds a message from a given existing file, consulting *options*, a parsed
    in memory version of the configuration settings that are applicable.

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

    m.computeIntegrity(path, o):

    In terms of consuming messages, the fields in the dictionary provide metadata
    for the announced resource. The anounced data could be embedded in the message itself,
    or available by a URL.

    Messages are generally gathered from a source such as the Message Queueing Protocol wrapper
    class: moth... sarracenia.moth. 


    data = m.getContent()

    will return the content of the announced resource as raw data.




   That's the entire message creation API.
"""


"""

  Time conversion routines.  
   - os.stat, and time.now() return floating point 
   - The floating point representation is a count of seconds since the beginning of the epoch.
   - beginning of epoch is platform dependent, and conversion to actual date is fraught (leap seconds, etc...)
   - Entire SR_* formats are text, no floats are sent over the protocol (avoids byte order issues, null byte / encoding 
issues, 
     and enhances readability.) 
   - str format: YYYYMMDDHHMMSS.msec goal of this representation is that a naive conversion to floats yields comparable 
numbers.
   - but the number that results is not useful for anything else, so need these special routines to get a proper epochal
 time.
   - also OK for year 2032 or whatever (rollover of time_t on 32 bits.)
   - string representation is forced to UTC timezone to avoid having to communicate timezone.

   timestr2flt - accepts a string and returns a float.


  caveat:
   - FIXME: this encoding will break in the year 10000 (assumes four digit year) and requires leading zeroes prior to 10
00.
     one will have to add detection of the decimal point, and change the offsets at that point.
    
"""


def nowflt():
    return timestr2flt(nowstr())


def nowstr():
    return timeflt2str(time.time())

def timeflt2str(f):
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


def durationToSeconds(str_value):
    """
   this function converts duration to seconds.
   str_value should be a number followed by a unit [s,m,h,d,w] ex. 1w, 4d, 12h
   return 0.0 for invalid string.
   """
    factor = 1

    if type(str_value) in [list]: 
        str_value=str_value[0]

    if type(str_value) in [int,float]: 
        return str_value

    if str_value[-1] in 'sS': factor *= 1
    elif str_value[-1] in 'mM': factor *= 60
    elif str_value[-1] in 'hH': factor *= 60 * 60
    elif str_value[-1] in 'dD': factor *= 60 * 60 * 24
    elif str_value[-1] in 'wW': factor *= 60 * 60 * 24 * 7
    if str_value[-1].isalpha(): str_value = str_value[:-1]

    try:
        duration = float(str_value) * factor
    except:
        logger.error("durationToSeconds, conversion failed for: %s" %
                     str_value)
        duration = 0.0

    return duration


def chunksize_from_str(str_value):
    #logger.debug("sr_config chunksize_from_str %s" % str_value)
    factor = 1
    if str_value[-1] in 'bB': str_value = str_value[:-1]
    if str_value[-1] in 'kK': factor = 1024
    if str_value[-1] in 'mM': factor = 1024 * 1024
    if str_value[-1] in 'gG': factor = 1024 * 1024 * 1024
    if str_value[-1] in 'tT': factor = 1024 * 1024 * 1024 * 1024
    if str_value[-1].isalpha(): str_value = str_value[:-1]
    chunksize = int(str_value) * factor

    return chunksize


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

    def computeIntegrity(msg, path, o):
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
        elif calc_method == 'arbitrary' :
            sumstr =  { 'method' : 'arbitrary', 'value': o.integrity_arbitrary_value }
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

        xattr.set('integrity', sumstr)
        xattr.persist()
        return sumstr

    def copyDict(msg, d):
       """
          copy dictionary into message.
       """
       if d is None: return

       for h in d:
            msg[h]=d[h]

    def dumps(msg):
       """
           FIXME: used to be msg_dumps.
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
    
    @staticmethod
    def fromFileData( path, o, lstat=None ):
        """
            create a message based on a given file, calculating the checksum.
            returns a well-formed message, or none.
        """
        m = sarracenia.Message.fromFileInfo( path, o, lstat )
        m['integrity'] = m.computeIntegrity( path, o )
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
    
        #FIXME no variable substitution... o.set_dir_pattern ?
     
        if hasattr(o,'post_exchange'):
            msg['exchange'] = o.post_exchange
        elif hasattr(o,'exchange'):
            msg['exchange'] = o.exchange
    
        msg['local_offset'] = 0
        msg['_deleteOnPost'] = set ( [ 'exchange', 'local_offset' ] )
    
        # notice
        msg['pubTime'] = timeflt2str(time.time())
    
        # set new_dir, new_file, new_subtopic, etc...
        msg.updatePaths( o, os.path.dirname(path), os.path.basename(path) )
    
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
    
        if o.integrity_method.startswith('cod,'):
            msg['integrity'] = { 'method':'cod', 'value':o.integrity_method[4:] }
        elif o.integrity_method in [ 'md5name', 'random' ]:
            algo = sarracenia.integrity.Integrity.factory(o.integrity_method)
            algo.set_path( post_relPath )
            msg['integrity'] = { 'method':o.integrity_method, 'value':algo.value }

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
    def fromStream( path, o, data=None ):
        """
           Create a file and message for the given path.  
           The file will be created or overwritten with the provided data.
           then invoke fromFileData() for the resulting file.
        """

        with open(path, 'wb') as fh:
            fh.write(data)

        if hasattr(o,'chmod') and o.chmod:
            os.chmod( path, o.chmod )

        return sarracenia.Message.fromFileData( path, o, os.stat(path) )
    
    
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
            logger.warning('unknown report code supplied: %d:%s' % (code, text))
            if text is None:
                text = 'unknown disposition'
    
        if 'report' in msg:
           logger.warning('overriding initial report: %d: %s' % ( msg['report']['code'], msg['report']['message'] ) )
    
        msg['_deleteOnPost'] |= set(['report'])
        msg['report'] = { 'code' : code, 'message': text }
    

    # ==============================================
    # how will the download file land on this server
    # with all options, this is really tricky
    # ==============================================

    def updateFieldsAccepted(msg, options, urlstr, pattern, maskDir,
                             maskFileOption, mirror, strip, pstrip, flatten):
        """
           Set new message fields according to values when the message is accepted.
           
           options - the sarracenia.config instance giving all the current configuration.
           urlstr - the urlstr being matched (baseUrl+relPath+sundew_extension)
           pattern - the regex that was matched.
           maskDir - the current directory to base the relPath from.
           maskFileOption - filename option value (sundew compatibility options.)
           strip  - number of path entries to strip from the left side of the path.
           pstrip - pattern strip regexp to apply instead of a count.
           flatten - a character to replace path separators with toe change 
                     a multi-directory deep file name into a single long file name
        """

        # relative path by default mirror
        if type(maskDir) is str:
            # trying to subtract maskDir if present in relPath...
            # occurs in polls a lot.
            if maskDir in msg['relPath']:
                 relPath = '%s' % msg['relPath'].replace(maskDir,'',1)

            # sometimes the same, just the leading / is missing.
            elif maskDir[1:] in msg['relPath']:
                 relPath = '%s' % msg['relPath'].replace(maskDir[1:],'',1)
            else:
                relPath = '%s' % msg['relPath']
        else:
            relPath = '%s' % msg['relPath']

        if options.baseUrl_relPath :
            u = urllib.parse.urlparse( msg['baseUrl'] )
            relPath = u.path[1:] + '/' + relPath

        # FIXME... why the % ? why not just assign it to copy the value?
        if 'rename' in msg: relPath = '%s' % msg['rename']

        token = relPath.split('/')
        filename = token[-1]


        # if provided, strip (integer) ... strip N heading directories
        #         or  pstrip (pattern str) strip regexp pattern from relPath
        # cannot have both (see setting of option strip in sr_config)

        if strip > 0:
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

        if maskFileOption is not None:
            try:
                filename = options.sundew_getDestInfos(msg, maskFileOption, filename)
            except:
                logger.error("problem with accept file option %s" %
                             maskFileOption)
            token[-1] = [filename]

        # MG this was taken from the sr_sender when not derived from sr_subscribe.
        # if a desftn_script is set in a plugin, it is going to be applied on all file
        # this might be confusing

        if options.destfn_script:
            options.new_file = filename
            ok = options.destfn_script(options)
            if filename != options.new_file:
                logger.debug("destfn_script : %s becomes %s " %
                             (filename, options.new_file))
                filename = options.new_file
                token[-1] = [filename]

        # not mirroring

        if not mirror:
            token = [filename]

        # uses current dir

        #if options.currentDir : new_dir = options.currentDir
        if maskDir:
            new_dir = options.set_dir_pattern(maskDir,msg)
        else:
            new_dir = ''

        if options.baseDir:
            if new_dir :
                d=new_dir
            elif options.post_baseDir:
                d=options.set_dir_pattern(options.post_baseDir,msg)
            else:
                d=None

            if d:
                for f in [ 'link', 'oldname', 'newname' ]:
                    if f in msg:
                        msg[f] = msg[f].replace( options.baseDir, d )

        # add relPath

        if len(token) > 1:
            new_dir = new_dir + '/' + '/'.join(token[:-1])

        new_dir = options.set_dir_pattern(new_dir, msg)
        # resolution of sundew's dirPattern

        tfname = filename
        # when sr_sender did not derived from sr_subscribe it was always called
        new_dir = options.sundew_dirPattern(pattern, urlstr, tfname, new_dir)

        msg.updatePaths( options, new_dir, filename )




    def updatePaths( msg, options, new_dir, new_file ):
        """
        set the new_ fields in the message based on changed file placement.

        If you change file placement in a flow callback, for example.
        One would change new_dir and new_file in the message.
        This routines updates other fields in the message (e.g. relPath, 
        baseUrl, topic ) to match new_dir/new_file.

        msg['post_baseUrl'] defaults to msg['baseUrl']
     
        """

        msg['_deleteOnPost'] |= set( ['new_dir', 'new_file', 'new_relPath', 'new_baseUrl', 'new_subtopic'] )
        msg['new_dir'] = new_dir
        msg['new_file'] = new_file

        relPath = new_dir + '/' + new_file

        if options.post_baseUrl:
            baseUrl_str = options.set_dir_pattern( options.post_baseUrl, msg )
        else:
            if 'baseUrl' in msg:
                baseUrl_str = msg['baseUrl']
            else:
                logger.error('missing post_baseUrl setting' )
                return
 
        if hasattr(options, 'post_baseDir') and ( type(options.post_baseDir) is str ) \
            and ( len(options.post_baseDir) > 1):
            pbd_str = options.set_dir_pattern( options.post_baseDir, msg )
            parsed_baseUrl = urllib.parse.urlparse(baseUrl_str)

            relPath = new_dir.replace( pbd_str, '', 1) + '/' + new_file

            if (len(parsed_baseUrl.path) > 1):
                relPath=relPath.replace( parsed_baseUrl.path, '', 1 )

        msg['new_baseUrl'] = baseUrl_str

        if relPath[0] == '/' :
            relPath = relPath[1:]

        msg['new_relPath'] = relPath
        msg['new_subtopic' ] = relPath.split('/')[0:-1]

        for i in [ 'relPath', 'subtopic', 'baseUrl' ]:
            if not i in msg:
               msg[ i ]= msg[ 'new_%s' % i ] 
        
        if sys.platform == 'win32':
            if 'new_dir' not in msg:
                msg['new_dir'] = msg['new_dir'].replace('\\', '/')
            msg['new_relPath'] = msg['new_relPath'].replace('\\', '/')
            if re.match('[A-Z]:', str(options.currentDir), flags=re.IGNORECASE):
                msg['new_dir'] = msg['new_dir'].lstrip('/')
                msg['new_relPath'] = msg['new_relPath'].lstrip('/')


    def validate(msg):
        """
        FIXME: used to be msg_validate
        return True if message format seems ok, return True, else return False, log some reasons.
        """
        if not type(msg) is sarracenia.Message:
            return False
    
        res=True
        for required_key in [ 'pubTime', 'baseUrl', 'relPath', 'integrity' ]:
            if not required_key in msg:
               logger.error('missing key: %s' % required_key )
               res=False
        if not res:
            logger.error('malformed message: %s', msg )
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

