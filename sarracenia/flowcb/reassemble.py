"""
 re-assemble files transferred as partitions.

 author: Peter Silva
"""

import flufl.lock
import humanfriendly
import logging
import os
import re
import stat
import time

from sarracenia import nowflt
import sarracenia
import sarracenia.filemetadata

from sarracenia.flowcb import FlowCB

from sarracenia.featuredetection import features

features['reassemble'] = { 'modules_needed': [ 'flufl.lock' ], 'Needed': True,
        'lament' : 'need to lock block segmented files to put them back together',
        'rejoice' : 'can reassemble block segmented files transferred' }

try:
    import flufl.lock
    features['reassemble']['present'] = True
except:
    features['reassemble']['present'] = False


logger = logging.getLogger(__name__)


class Reassemble(FlowCB):
    """
     if you see receive partitioned files (with §block_... _§ at the end of the file name)    
     then turning on this callback will have them re-assembled.


     usage:

        callback_prepend reassemble

        * whan a part is received but we are still waiting for more blocks, do the
          block file message is put in the rejected worklist.
        * only when all parts are received will a completed file be forwarded for
          processing by subsequent plugins, and posting for future consumer.

   limitations:

      inflight None  -- required.. doesn't work with tmp files.


    algorithm:
       given the reassemble setting is on, and have received a block file,
       then:

       * partition file is whose name ends in §block_<blokno>,<blocksize>_§
       * determing the inflight_file name for the entire file.
       * lock the inflight_file.
       * place the block in the working file.
       * update the manifest of the inflight_file.
       * delete the block file.
       * if the file is not yet complete, remove the message from the posting queue.
       * if all blocks of the file have been delivered
          * then make the message reflect the whole file.
          
    """
    def __init__(self, options) -> None:

        super().__init__(options,logger)

        #FIXME: missing metrics for now.
        self.metric_scanned = 0
        self.metric_hits = 0
       
    def after_work(self, worklist) -> None:

        if self.o.inflight:
            logger.error( f"partitioned file transfer only work with inflight None" )
            return

        new_ok=[]
        for m in worklist.ok:

            # this callback only operates on partition files.
            if not ('blocks' in m and m['relPath'].endswith('_§') ):
                new_ok.append(m)
                continue

            new_sz=0
            for b in m['blocks']['manifest']:
                new_sz+= m['blocks']['manifest'][b]['size']

            rp=m['relPath']
            blk_suffix=re.search( '§block_.*_§', rp ).group().split(',')
            if not len(blk_suffix) >= 2:
                logger.error( f"badly name block file, skipping {m['relPath']} " )
                new_ok.append(m)
                continue

            # assert: have a properly named block file.
            blkno=int(blk_suffix[0][7:])
            blksz=humanfriendly.parse_size(blk_suffix[1],binary=True)

            if blkno != m['blocks']['number']:
                logger.warning(" mismatch {m['relPath']} name says {blkno} but message says {m['block']['number']}" )
                blkno = m['blocks']['number']

            #determine root file name.
            part_file=m['new_dir'] + os.sep + m['new_file']

            # FIXME: could add code here to deal with inflight != none make root_file the inflight file.
            root_file=m['new_dir'] + os.sep + os.path.basename(rp[0:rp.find("§block_")])
            lock_file=root_file + '.flufl_lock'
                
            # FIXME: need to lock the file.
            flck = flufl.lock.Lock(lock_file)

            flck.lock()

            pf=open(part_file,'rb')

            if os.path.exists(root_file):
                rf=open(root_file,'r+b')
            else:
                rf=open(root_file,'w+b')

            old_stat = os.stat(root_file)

            old_blocks=None
            with sarracenia.filemetadata.FileMetadata(root_file) as xrfa:
                old_blocks = xrfa.get( 'blocks' )

            # calculate old file size.
            if old_blocks and 'manifest' in old_blocks:
                old_sz=0
                for b in old_blocks['manifest']:
                    old_sz += old_blocks['manifest'][b]['size']
            else:
                old_sz = old_stat.st_size

            # new file is shorter than before.
            if new_sz < old_sz:  
                logger.info( f"truncating to {new_sz}" )
                rf.truncate(new_sz)

            # update old_blocks to reflect receipt of this block.
            if old_blocks and 'manifest' in old_blocks:
                logger.info( f" read old block manifest from attributes: {old_blocks['manifest']}" )
                logger.info( f" also show waiting: {old_blocks['waiting']}" )
                found=False
                sz=0
                # add
                old_blocks['manifest'][blkno] = m['blocks']['manifest'][blkno] 
            else:
                logger.info( f"creating new block manifest for root_file " )
                old_blocks = { 'method': 'separate', 'size': m['blocks']['size'], 'number': blkno }
                old_blocks['waiting'] = m['blocks']['manifest'].copy()
                old_blocks['manifest'] = { blkno: m['blocks']['manifest'][blkno] }

            # no longer waiting for the block which has been received.

            if blkno in old_blocks['waiting']:
                del old_blocks['waiting'][blkno]
                logger.info( f"deleted block {blkno} from waiting: {old_blocks['waiting']} ") 

            # calculate where to seek to...
            offset=0
            i=0
            while i < blkno:
                thisblk = m['blocks']['manifest'][i]['size']
                offset += thisblk
                i+=1
            
            logger.info( f" disk manifest is: {old_blocks['manifest']}" )
            byteCount = m['blocks']['manifest'][blkno]['size']

            logger.info( f" blocks: adding block {blkno} by seeking to: {offset} to write {byteCount} bytes in {root_file}" )
            logger.info( f" still waiting for: {len(old_blocks['waiting'])} - {old_blocks['waiting']} " ) 

            # FIXME: can seek ever fail? how do we check?
            rf.seek(offset)     

            # copy data from block partition file into final destination.
            sz=self.o.bufsize if self.o.bufsize > byteCount else byteCount
            bytesTransferred=0
            while bytesTransferred < byteCount: 
                b = pf.read(sz)
                rf.write(b)
                bytesTransferred += len(b)
                bytesLeft = byteCount - bytesTransferred
                sz=self.o.bufsize if self.o.bufsize > bytesLeft else bytesLeft

            rf.close()
            pf.close()

            # assert: block data is now in main file, so delete block
            os.unlink(part_file)

            with sarracenia.filemetadata.FileMetadata(root_file) as xrfab:
                xrfab.set('mtime',m['mtime'])
                logger.info( f" about to persist...waiting: {old_blocks['waiting']} ")
                xrfab.set('blocks',old_blocks)

            if len( old_blocks['waiting'] ) > 0 :
                # do not re-post the message if it's only part that has been received.
                """
                206 Partial Content 
                   The server is delivering only part of the resource (byte 
                   serving) due to a range header sent by the client. The range
                   header is used by HTTP clients to enable resuming of 
                   interrupted downloads, or split a download into multiple 
                   simultaneous streams.
                   (from https://en.wikipedia.org/wiki/List_of_HTTP_status_codes)
                """
                m.setReport( 206, "file block subset received and reassembled ok. Not forwarding." )
                worklist.rejected.append(m)
            else:
                # FIXME: for inflight.  now rename the file to the real name.

                m['relPath'] = rp[0:rp.find("§block_")]
                m['new_file'] = m['new_file'][0:m['new_file'].find("§block_")]
                m['blocks']['method'] = 'inplace'
                del m['blocks']['number']
                m['size'] = new_sz
                new_ok.append(m)

            flck.unlock()

        worklist.ok = new_ok

    def on_housekeeping(self):
        logger.info( f'files scanned {self.metric_scanned}, hits: {self.metric_hits} ')
        self.metric_scanned = 0
        self.metric_hits = 0
