from sarracenia.identity import Identity

default_value = "None"


def set_default_value(value):
    global default_value
    default_value = value

class Arbitrary(Identity):
    """
      For applications where there is no known way of determining equivalence, allow them to supply
      an arbitrary tag, that can be used to compare products for duplicate suppression purposes.

      use setter to set the value... some sort of external checksum algorithm that cannot be reproduced.
     """
    def __init__(self):
        global default_value
        self._value = default_value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value

    @staticmethod
    def registered_as():
        return 'a'

    def set_path(self, path):
        pass

    def update(self, chunk):
        pass
