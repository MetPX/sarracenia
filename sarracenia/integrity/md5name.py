#!/usr/bin/env python3

from hashlib import md5

from base64 import b64encode

import logging

from sarracenia.integrity import Integrity

import os

logger = logging.getLogger(__name__)

class Md5name(Integrity):
    """
        *Fake* checksum... the md5 value being applied to the name of the file.
        suitable when files with the same name should be considered the same,
        even if they contain different bytes.
      """
    def registered_as():
        """
            v2name.
          """
        return 'n'

    def set_path(self, path):
        self.filename = os.path.basename(path)
        self.filehash = md5()
         
    def update(self, chunk ):
        self.filehash.update( bytes(self.filename, 'utf-8') )
