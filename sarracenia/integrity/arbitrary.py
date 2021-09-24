from sarracenia.integrity import Integrity


default_value = "None"

def set_default_value( value ):
    global default_value
    default_value = value
   
class Arbitrary(Integrity):
    """
      use set_value, to set the value... some sort of external checksum algorithm that cannot be reproduced.
     """
    def __init__(self):
        global default_value
        self.value = default_value

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def registered_as():
        return 'a'

    def set_path(self, path):
        pass

    def update(self, chunk):
        pass
