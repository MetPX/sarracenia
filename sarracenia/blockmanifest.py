
"""
 DEPENDENCY:
  should not be imported unless sarracenia.features['reassembly']['present'] is True
  (indicating that flufl.lock is installed.)

"""

import logging
import json
import flufl.lock
import os

logger = logging.getLogger(__name__)


class BlockManifest:

    """

      json i/o to a file, of a given dict, using locking to serialize updates.
      
      instantiate the object to lock read the file.

      get()/set() to see the values or change them.

      when it goes away, the file gets re-written with updated content, and is unlocked.


      Problems:

      - the locking is advisory... so only other reassemble modules will use it.
        if you have multiple subscribers, and another downloads the manifest, it can clobber
        the one being used by re-assemble.

      - to avoid that:

        * have the block_manifest used by reassembly be named block_reassembly? but if a watch
          sees that, then same issue arises.

        * never download block_manifest (currently there are rejects for the block_manifest files)
          (requires that manifest be in the message.)

        * leaves manifests everywhere... should I have options:
          * don't write the manifest to disk
          * erase the manifest once you're done.
          * rebuild the manifest, if it's missing, from disk.


       TODO:

       * uses flufl.lock with feature guards.
       * look at flowcb/block_reassembly.py


    """


    def __init__(self,path):
        """
            lock the path, read the data, leave it ready to be re-written. 
            still locked.
        """

        if '§block_' in path: # replace block suffix with manifest suffice if needbe.
            pp=path.split('§')
            self.path= '§'.join(pp[0:-2]) + '§block_manifest§'
        else:
            self.path=path + '§block_manifest§'

        self.lock_file = self.path + '.flufl_lock'

        self.lock = flufl.lock.Lock(self.lock_file)

        self.lock.lock()

        self.x = {}
        self.new_x = {}

        if os.path.exists(self.path):
            self.fd = open(self.path,"r+")
            s=self.fd.read()
            try:
                self.x = json.loads(s)
            except Exception as ex:
                pass

            for k in ['manifest', 'waiting' ]:
                if k in self.x:
                    m={}
                    for db in self.x[k]: # when json'd for writing, numeric indices are stringified.
                        m[db if type(db) is int else int(db)] = self.x[k][db]
                    self.x[k] = m
        else:
            self.fd = open(self.path,"w+")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.persist()

    def __del__(self):
        self.persist()

    def get(self):
        """
            return the value of the block manifest.
        """
        if self.new_x:
            return self.new_x
        elif self.x:
            return self.x
        return None


    def set(self,bm):
        """

        """
        self.new_x=bm.copy()
        if "number" in self.new_x:
            del self.new_x['number']

    def persist(self):
       """
          write the new data, release the lock.
       """
       if not self.fd:
           return

       if self.new_x and (self.new_x != self.x):
           self.fd.seek(0)
           self.fd.write(json.dumps(self.new_x,sort_keys=True,indent=4))
           self.fd.truncate()

       self.fd.close()
       self.lock.unlock()
       self.fd=None

