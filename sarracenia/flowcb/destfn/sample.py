"""

  a destfn plugin script is used by senders or subscribers to do complex file naming.
  this is an API demonstrator that prefixes the name delivered with 'renamed\\_'::

     filename DESTFNSCRIPT=sarracenia.flowcb.destfn.sample.Sample

  An alternative method of invocation is to apply it selectively::

     accept k* DESTFNSCRIPT=sarracenia.flowcb.destfn.sample.Sample

  As with other flowcb plugins, the import will be done using normal
  python import mechanism equivalent to::

     import sarracenia.flowcb.destfn.sample

  and then in that class file, there is a Sample class, the sample class
  contains the destfn method, or entry_point.
 
  The destfn routine consults the fields in the given message, and based on them,
  return a new file name for the file to have after transfer (download or send.)

  the routines have access to the settings via options provided to init,
  accessed, by convention, as self.o.

  The routine can also modify fields create new ones in the message.

  the destfn routine returns the new name of the file.

"""

import logging

from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)

class Sample(FlowCB):

      def destfn(self,msg) -> str:

          logger.info('before: m=%s' % msg )
          relPath = msg["relPath"].split('/')
          msg['destfn_added_prefix'] = 'renamed_'
          return 'renamed_' + relPath[-1]

