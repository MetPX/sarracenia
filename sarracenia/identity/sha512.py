from hashlib import sha512

from sarracenia.identity import Identity

# ===================================
# checksum_s class
# ===================================


class Sha512(Identity):
    """
      The SHA512 algorithm to checksum the entire file, which is called 's'.
      """

    @staticmethod
    def registered_as():
        return 's'

    def set_path(self, path):
        self.filehash = sha512()

    def update(self, chunk):
        if type(chunk) == bytes: self.filehash.update(chunk)
        else: self.filehash.update(bytes(chunk, 'utf-8'))
