#!/usr/bin/env python3

from hashlib import md5

from base64 import b64decode, b64encode

from sarra.plugin.integrity import Integrity


class Md5name(Integrity):
      """
        *Fake* checksum... the md5 value being applied to the name of the file.
        suitable when files with the same name should be considered the same,
        even if they contain different bytes.
      """
      @classmethod
      def assimilate(cls,obj):
         obj.__class__ = Md5name

      def __init__(self):
         Md5name.assimilate(self)

      def registered_as():
          """
            v2name.
          """
          return 'n'

      def set_path(self,path):
          filename   = os.path.basename(path)
          self.value = b64encode(md5(bytes(filename,'utf-8'))).decode('utf-8')

