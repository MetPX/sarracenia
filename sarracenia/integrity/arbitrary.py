from sarracenia.integrity import Integrity


class Arbitrary(Integrity):
    """
      use set_value, to set the value... some sort of external checksum algorithm that cannot be reproduced.
     """
    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def registered_as():
        return 'a'
