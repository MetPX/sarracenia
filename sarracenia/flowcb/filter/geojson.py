"""
  This plugin delays processing of messages by *message_delay* seconds

  sarracenia.flowcb.msg.fdelay 30
  import sarracenia.flowcb.filter.fdelay.Fdelay

  or more simply:

  fdelay 30
  callback filter.fdelay

  every message will be at least 30 seconds old before it is forwarded by this plugin.
  in the meantime, the message is placed on the retry queue by marking it as failed.

"""
import logging

from sarracenia.flowcb import FlowCB

import json

logger = logging.getLogger(__name__)


class GeoJSON(FlowCB):
    def __init__(self, options):

        super().__init__(options,logger)

        logging.basicConfig(format=self.o.logFormat,
                            level=getattr(logging, self.o.logLevel.upper()))

        self.o.add_option('geometry', 'list', [])

        self.geometry_geojson = None
        if hasattr(self.o, 'geometry') and self.o.geometry != []:
            try:
                self.geometry_geojson = json.loads("\n".join(self.o.geometry))
            except json.decoder.JSONDecodeError as err:
                logger.error(f"error parsing geometry from configuration file: {err}")
                raise

    def after_accept(self, worklist):
        outgoing = []

        for m in worklist.incoming:
            
            #if geometry isn't configured, or the message doesn't have geometry
                #reject the message, and continue
            if 'geometry' not in m or self.geometry_geojson == None:
                logger.debug('No geometry found in message, or geometry not configured; rejecting')
                worklist.rejected.append(m)
                continue

            #Parse the message geometry field, and Json-ize it
            try:
                #We're just going to trust that geometry is a properly formatted GeoJSON object
                # Ultimately, if it's not, some of the logic in following sections will fail, and we'll have to catch those errors then
                message_geometry = json.loads(m['geometry'])
            except json.decoder.JSONDecodeError as err:
                logger.error(f"error parsing message geometry: {err}")
            
            geomotries_overlap = False
            try:
                # do the comparison, and figure out if the configured geometry contains the message's
                pass

            except err:
                # catch comparison errors, and add to "failed", logging a message
                worklist.failed.append(m)
                logger.error(f"error comparing: {err}")
                continue
            

            if geomotries_overlap:
            # If the message's GeoJSON point is in/intersects with the configured GeoJSON
                #add the message to outgoing
                outgoing.append(m)
            else:
                #add to rejected?
                worklist.rejected.append(m)

        worklist.incoming = outgoing