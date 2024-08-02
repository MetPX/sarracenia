import random

from sarracenia.identity import Identity


class Random(Identity):
    """
      Trivial minimalist checksumming algorithm, returns random number for any file.
      """
    @property
    def value(self):
        return '%.4d' % random.randint(0, 9999)

    def set_path(self, path):
        pass

    @staticmethod
    def registered_as():
        return '0'

    def update(self, chunk):
        pass

