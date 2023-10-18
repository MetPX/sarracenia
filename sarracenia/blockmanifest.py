

import logging
import json
import flufl.lock
import os

logger = logging.getLogger(__name__)


class BlockManifest:

    """

      json i/o to a file, of a given dict, using locking to serialize updates.
      
      there might be an API to reconcile...
         -- compare what is on disk to what is in memory.

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

        logger.info( f"FIXME! locking with: {self.lock_file}" )
        self.lock = flufl.lock.Lock(self.lock_file)

        self.lock.lock()
        logger.info( "FIXME! locked." )

        self.x = None
        self.new_x = None

        if os.path.exists(self.path):
            self.fd = open(self.path,"r+")
            logger.info( f" self.fd: {self.fd} " )
            s=self.fd.read()
            logger.info( f" manifest content: {s} " )
            self.x = json.loads(s)
            logger.info( f" read self.x: {self.x} " )

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
           logger.info( f"FIXME! overwriting" )
           self.fd.seek(0)
           self.fd.write(json.dumps(self.new_x,sort_keys=True,indent=4))
           self.fd.truncate()
       else:
           logger.info( f"FIXME! closing unchanged" )

       self.fd.close()
       logger.info( f"FIXME! unlocking " )
       self.lock.unlock()
       self.fd=None

