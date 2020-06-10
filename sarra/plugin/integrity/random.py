#!/usr/bin/env python3

import random

from sarra.plugin.integrity import Integrity


class Random(Integrity):
      """
      Trivial minimalist checksumming algorithm, returns random number for any file.
      """
      @classmethod
      def assimilate(cls,obj):
         obj.__class__ = Random

      def __init__(self):
         Random.assimilate(self)

      def get_value(self):
          return '%.4d' % random.randint(0,9999)

      def registered_as():
          return '0'

