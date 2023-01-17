
"""
   A destfn script to do string replacement.

Sample usage in a config file:

    destfn_replace 1stStringToReplace,replacementOf1st
    destfn_replace SRCN,sssssRCCCn

    accept .*SRCN.* DESTFNSCRIPT=destfn.replace

    # files that do not match 
    accept .*



"""

import logging

from sarracenia.flowcb import FlowCB

logger = logging.getLogger(__name__)



class Replace(FlowCB):

      def __init__(self,options):
          super().__init__(options,logger)
          self.o.add_option('destfn_replace','list' )

      def destfn(self,msg) -> str:

          old_name=msg["relPath"].split('/')[-1]
          new_name=old_name
          for r in self.o.destfn_replace:
               (before,after) = r.split(',')
               new_name = new_name.replace( before, after, 1)
          logger.info('from: %s,  to: %s' % (old_name, new_name ))
 
          return new_name

