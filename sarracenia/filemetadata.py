# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
#
# sr_post.py : python3 program allowing users to post an available product
#
# Code contributed by:
#  Michel Grenier - Shared Services Canada
#  Last Changed   : Nov  8 22:10:16 UTC 2017
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

try:
    import xattr
    supports_extended_attributes = True

except:
    supports_extended_attributes = False

import sys

supports_alternate_data_streams = False

if sys.platform == 'win32':
    try:
        from sarracenia.pyads import ADS
        supports_alternate_data_streams = True

    except:
        pass

import json

STREAM_NAME = 'sr_.json'

xattr_disabled = False


def disable_xattr():
    global xattr_disabled
    xattr_disabled = True


class FileMetadata:
    """
      This class implements storing metadata *with* a file.

      on unlix/linux/mac systems, we use extended attributes,
      where we apply a *user.sr_* prefix to the attribute names to avoid clashes.
    
      on Windows NT, create an "sr_.json" Alternate Data Stream  to store them.

      API:
    
      All values are utf-8, hence readable by some subset of humans. 
      not bytes.  no binary, go away...

      x = sr_attr( path )  <- read metadata from file.
      x.list()  <- list all extant extended attributes.
       sample return value: [ 'sum', 'mtime' ]
      x.get('sum') <- look at one value.
         returns None if missing.
      x.set('sum', 'hoho') <- set one value.
         fails silently (fall-back gracefully.)
      x.persist() <- write metadata back to file, if necessary.

   """
    def __init__(self, path):

        global supports_alternate_data_streams
        global supports_extended_attributes

        self.path = path
        self.x = {}
        self.dirty = False

        if xattr_disabled:
            supports_alternate_data_streams = False
            supports_extended_attributes = False
            return

        if supports_alternate_data_streams:
            self.ads = ADS(path)
            s = list(self.ads)
            if STREAM_NAME in s:
                self.x = json.loads(
                    self.ads.get_stream_content(STREAM_NAME).decode('utf-8'))

        if supports_extended_attributes:
            d = xattr.xattr(path)
            for i in d:
                if not i.startswith('user.sr_'):
                    continue
                k = i.replace('user.sr_', '')
                v = d[i].decode('utf-8')
                self.x[k] = v

    def __del__(self):
        self.persist()

    """
     return a dictionary of extended attributes.

   """

    def list(self):
        return self.x.keys()

    def get(self, name):
        if name in self.x.keys():
            return self.x[name]
        return None

    def set(self, name, value):
        self.dirty = True
        self.x[name] = value

    def persist(self):

        global supports_alternate_data_streams
        global supports_extended_attributes

        if not self.dirty:
            return

        try:
            if supports_alternate_data_streams:

                #replace STREAM_NAME with json.dumps(self.x)
                s = list(self.ads)
                if STREAM_NAME in s:
                    self.ads.delete_stream(STREAM_NAME)

                self.ads.add_stream_from_string(
                    STREAM_NAME, bytes(json.dumps(self.x, indent=4), 'utf-8'))

            if supports_extended_attributes:
                #set the attributes in the list. encoding utf8...
                for i in self.x:
                    xattr.setxattr(self.path, 'user.sr_' + i,
                                   bytes(self.x[i], 'utf-8'))
        except:
            # not really sure what to do in the exception case...
            # permission would be a normal thing and just silently fail...
            # could also be on windows, but not on an NTFS file system.
            # silent failure means it falls back to using other means.
            pass

        self.dirty = False
