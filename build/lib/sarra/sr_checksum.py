#!/usr/bin/env python3

"""

A single checksum class is chosen by the source of data being injected into the network.
The following checksum classes are alternatives that are built-in.  Sources may define 
new algorithms that need to be added to networks.

checksums are used by:
    sr_post to generate the initial post.
    sr_post to compare against cached values to see if a given block is the same as what was already posted.
    sr_sarra to ensure that the post received is accurate before echoing further.
    sr_subscribe to compare the post with the file which is already on disk.
    sr_winnow to determine if a given post has been seen before.


The API of a checksum class (in calling sequence order):
   __init__      -- initialize the value of a checksum for a part.
   get_value     -- return the current calculated checksum value.
   registered_as -- return the letter or string under which this checksum is named in post message
   set_path      -- identify the checksumming algorithm to be used by update.
   update        -- given this chunk of the file, update the checksum for the part

The API allows for checksums to be calculated while transfer is in progress 
rather than after the fact as a second pass through the data.  

"""

# ===================================
# checksum class
# ===================================

class sr_checksum(object):
      """
      The default algorithm is to do a checksum of the entire contents of the file, which is called 'd'.
      """
      def __init__(self):
          self.value = None

      def get_value(self):
          return self.value

      def registered_as(self):
          return None

      def set_path(self,path):
          pass

      def update(self,chunk):
          pass

