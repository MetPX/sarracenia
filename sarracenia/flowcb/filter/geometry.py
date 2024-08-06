"""
    This plugin filters messages based on geo-location.
    Specifically, by comparing configured GeoJSON objects, with those found in messages

    geometry {"type": "Polygon",
    geometry  "coordinates": [
    geometry     [
    geometry        [-10.0, -10.0],
    geometry        [10.0, -10.0],
    geometry        [10.0, 10.0],
    geometry        [-10.0, -10.0]
    geometry    ]
    geometry  ]
    geometry }

    # geometry_maxDistance is in Kilometers
    geometry_maxDistance 1.5

"""
import logging

from sarracenia.flowcb import FlowCB

from sarracenia.featuredetection import features

features['geometry'] = { 'modules_needed': ['geojson', 'turfpy'], 'present': False, 
        'lament': 'cannot filter messages based on geojson coordinates' ,
        'rejoice': 'able to filter messages based on geojson coordinates' }

try:
    import json
    from turfpy.measurement import distance, boolean_point_in_polygon
    from turfpy.transformation import intersect
    from geojson import Point, Feature, Polygon, FeatureCollection
    features['geometry']['present'] = True
except:
    features['geometry']['present'] = False


logger = logging.getLogger(__name__)


class Geometry(FlowCB):
    def __init__(self, options):

        super().__init__(options,logger)

        logging.basicConfig(format=self.o.logFormat,
                            level=getattr(logging, self.o.logLevel.upper()))

        self.o.add_option('geometry', 'list', [])
        self.o.add_option('geometry_maxDistance', 'float', -1)

        self.geometry_geojson = None
        if hasattr(self.o, 'geometry') and self.o.geometry != []:
            try:
                self.geometry_geojson = json.loads("\n".join(self.o.geometry))
            except json.decoder.JSONDecodeError as err:
                logger.error(f"error parsing geometry from configuration file: {err}")
                raise
                

    def after_accept(self, worklist):
        accepted = []

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
                logger.error(f"error parsing message geometry: {err}; {m}")
                raise
            

            accept_message = False
            try:
                if message_geometry['type'] == "Point" and self.geometry_geojson['type'] == "Point":
                    #calculate distance between points, and check if it's less <= maxDistance
                    if self.o.geometry_maxDistance <= 0:
                        logger.warning(f"maxDistance is negative, so we can't compare distances")
                        worklist.failed.append(m)
                        continue
                    
                    #check if the distance between points is less than or equal to 'self.o.geometry_maxDistance'
                    start = Feature(geometry=Point(message_geometry['coordinates']))
                    end = Feature(geometry=Point(self.geometry_geojson['coordinates']))
                    
                    accept_message = (distance(start, end) <= self.o.geometry_maxDistance)
                    
                elif message_geometry['type'] == "Polygon" and self.geometry_geojson['type'] == "Point":  
                    #Check if configured point is inside the message polygon
                    poly = Feature(geometry=Polygon(message_geometry['coordinates']))
                    point = Feature(geometry=Point(self.geometry_geojson['coordinates']))
                    
                    accept_message = boolean_point_in_polygon(point, poly)

                elif message_geometry['type'] == "Point" and self.geometry_geojson['type'] == "Polygon": 
                    #Check if configured plygon contains the message point
                    point = Feature(geometry=Point(message_geometry['coordinates']))
                    poly = Feature(geometry=Polygon(self.geometry_geojson['coordinates']))
                    
                    accept_message = boolean_point_in_polygon(point, poly)

                elif message_geometry['type'] == "Polygon" and self.geometry_geojson['type'] == "Polygon": 
                    #Check if configured plygon intersects message polygon
                    poly1 = Feature(geometry=Polygon(self.geometry_geojson['coordinates']))
                    poly2 = Feature(geometry=Polygon(message_geometry['coordinates']))

                    accept_message = bool(intersect(FeatureCollection([poly1, poly2])))
                # catch cases for when neither the config or the message have points or poylgons (multipoint, line, etc..)
                else:
                    logger.debug(f"Message or config aren't a Point or Polygon, failing; message={m}")
                    worklist.failed.append(m)
                    continue
                

            except Exception as err:
                # catch comparison errors, and add to "failed", logging a message
                worklist.failed.append(m)
                logger.error(f"error comparing: {err}; message={m}")
                continue
            

            if accept_message:
            # If the message's GeoJSON point is in/intersects with the configured GeoJSON
                #add the message to outgoing
                accepted.append(m)
                logger.debug("Geometries overlap, or points are closer than maxDistance; accepting")
            else:
                #add to rejected?
                worklist.rejected.append(m)
                logger.debug("Geometries don't overlap, or points are farther than maxDistance; rejecting")

        worklist.incoming = accepted