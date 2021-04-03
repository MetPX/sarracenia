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
__version__ = "3.00.05"

import logging

logger = logging.getLogger(__name__)

import calendar
import datetime
import time
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

   timeflt2str - accepts a float and returns a string.
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
    nsec = "{:.9g}".format(f % 1)[1:]
    return "{}{}".format(time.strftime("%Y%m%d%H%M%S", time.gmtime(f)), nsec)


def v3timeflt2str(f):
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
    503: "Service unavailable. delete (File removal not currently supported.)",
    503: "Unable to process: Service unavailable",
    503: "Unsupported transport protocol specified in posting."
}


def msg_set_report(msg, code, text=None):
    """
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

    if not 'report' in msg:
        msg['report'] = code
        msg['message'] = text
        msg['_deleteOnPost'] |= set(['report', 'message'])
    else:
        msg['report'] = code
        msg['message'] += text
