#!/usr/bin/env python3

import random

from sarracenia.integrity import Integrity


class Random(Integrity):
    """
      Trivial minimalist checksumming algorithm, returns random number for any file.
      """
    def get_value(self):
        return '%.4d' % random.randint(0, 9999)

    def registered_as():
        return '0'
