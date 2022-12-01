"""
Plugin sundewpxroute.py:
    Implement message filtering based on a routing table from MetPX-Sundew.
    Make it easier to feed clients exactly the same products with sarracenia,
    that they are used to with sundew.

Usage:
    the pxrouting option must be set in the configuration before the plugin
    is configured, like so:
    * pxRouting /local/home/peter/src/pdspx/routing/etc/pxRouting.conf
    * pxClient  navcan-amis
    flowcb sarracenia.flowcb.accept.sundewpxroute.SundewPxRoute
"""

import logging

from sarracenia.flowcb import FlowCB
logger = logging.getLogger(__name__)


class SundewPxRoute(FlowCB):
    def __init__(self, options):
        """

          For World Meteorological Organization message oriented routing.
          Read the configured metpx-sundew routing table, and figure out which
          Abbreviated Header Lines (AHL's) are configured to be sent to 'target'
          being careful to account for membership in clientAliases.

          init sets 'ahls_to_route' according to the contents of pxrouting

        """
        self.o = options
        self.ahls_to_route = {}

        pxrf = open(self.o.pxRouting[0], 'r')
        possible_references = self.o.pxClient[0].split(',')
        logger.info("sundew_pxroute, target clients: %s" % possible_references)

        for line in pxrf:
            words = line.split()

            if (len(words) < 2) or words[0] == '#':
                continue

            if words[0] == 'clientAlias':
                expansion = words[2].split(',')
                for i in possible_references:
                    if i in expansion:
                        possible_references.append(words[1])
                        logger.debug( "sundew_pxroute adding clientAlias %s to possible_reference %s"  % \
                                (words[1], possible_references) )
                        continue

            if words[0] == 'key':
                expansion = words[2].split(',')
                for i in possible_references:
                    if i in expansion:
                        self.ahls_to_route[words[1]] = True
        pxrf.close()

        logger.debug(
            "sundew_pxroute For %s, the following headers are routed %s" %
            (self.o.pxClient[0], self.ahls_to_route.keys()))

    def after_accept(self, worklist):
        new_incoming = []

        for message in worklist.incoming:
            ahl = message.new_file.split('/')[-1][0:11]

            if (len(ahl) < 11) or (ahl[6] != '_'):
                logger.debug("sundew_pxroute not an AHL: %s, " % ahl)
                worklist.rejected.append(message)
                continue
            if (ahl in self.ahls_to_route.keys()):
                logger.debug("sundew_pxroute yes, deliver: %s, " % ahl)
                new_incoming.append(message)
                continue
            else:
                logger.debug("sundew_pxroute no, do not deliver: %s, " % ahl)
                worklist.rejected.append(message)
        worklist.incoming = new_incoming
