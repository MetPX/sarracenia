#!/usr/bin/env python3

"""
  Implement message filtering based on a routing table from MetPX-Sundew.
  Make it easier to feed clients exactly the same products with sarracenia,
  that they are used to with sundew.  

"""

class SundewRoute(object):


    def __init__(self):

 
        """

          For World Meteorological Organization message oriented routing.
          Read the configured metpx-sundew routing table, and figure out which
          Abbreviated Header Lines (AHL's) are configured to be sent to 'target'
          being careful to account for membership in clientAliases.

        """
        self.pxroute="/local/home/peter/src/pdspx/routing/etc/pxRouting.conf"
        self.target='navcan-amis'
        self.ahls_to_route={}

        pxrf=open(self.pxroute,'r')
        possible_references=[ self.target ]

        for line in pxrf:
            #print("line: ", line)
            words = line.split()
            
            if (len(words) < 2) or words[0] == '#' : 
               continue
        
            if words[0] == 'clientAlias':
                #print( "clientAlias %s" % words[1] );
                expansion = words[2].split(',')
                #print( "expansion: %s" % expansion )
                for i in possible_references :
                    if i in expansion:
                       possible_references.append( words[1] )
                       #print( "adding clientAlias %s to possible_reference %s, for target %s"  % \
                       #        (words[1], possible_references, target) )
                       continue
                    
            if words[0] == 'key' :
                expansion = words[2].split(',')
                for i in possible_references :
                    if i in expansion:
                       self.ahls_to_route[ words[1] ] = True
        
                #print( "key %s" % words[1] );
        
        pxrf.close()
        
        #print( "For %s, the following headers are routed %s" % ( self.target, self.ahls_to_route.keys() ) )
        
    def perform(self,parent):
        logger = parent.logger
        msg    = parent.msg
        
        ahl = msg.local_file.split('/')[-1][0:11]

        if ( len(ahl) < 11 ) or ( ahl[6] != '_' ): 
            logger.debug("sundewroute not an AHL: %s, " % ahl )
            return False

        if ( ahl in self.ahls_to_route.keys() ) :
            logger.debug("sundewroute yes, deliver: %s, " % ahl )
            return True
        else:
            logger.debug("sundewroute no, do not deliver: %s, " % ahl )
            return False


parent=Parent()
sundewroute.perform(parent)


