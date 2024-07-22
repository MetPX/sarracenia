
import pytest
import types
import json
from tests.conftest import *
#from unittest.mock import Mock

import sarracenia.config
import sarracenia.flowcb.filter.geometry

from sarracenia import Message as SR3Message
import sarracenia.config

# poly2 intersects poly1 (poly2 is *inside* poly1)
# poly3 doesn't intersect ploy1 or poly2
# pointA is inside poly1 and poly2, but outside poly3
# pointB is exactly 14.37 from pointA, and outside all polys
features = {
    "poly1": '{"type": "Polygon", "coordinates": [[[-75.833, 39.284], [-75.332, 39.284], [-75.332, 40.584], [-75.833, 40.584], [-75.833, 39.284]]]}',
    "poly2": '{"type": "Polygon", "coordinates": [[[-75.833, 39.0], [-75.332, 39.0], [-75.332, 40.0], [-75.833, 40.0], [-75.833, 39.0]]]}',
    "poly3": '{"type": "Polygon", "coordinates": [[[-75.23416523236531, 39.995004507255146], [-75.24210552549602, 39.74740546271903], [-74.77443322056371, 39.74975378649694], [-74.7732973552161, 39.98320146676278], [-75.23416523236531, 39.995004507255146]]]}',
    "pointA": '{"type": "Point", "coordinates": [-75.833, 39.284]}',
    "pointB": '{"type": "Point", "coordinates": [-76, 39.284]}',
    "pointC": '{"type": "Point", "coordinates": [93]}',
    "line1": '{"type": "LineString", "coordinates": [93, 100]}',
}

def make_worklist():
    WorkList = types.SimpleNamespace()
    WorkList.ok = []
    WorkList.incoming = []
    WorkList.rejected = []
    WorkList.failed = []
    WorkList.directories_ok = []
    return WorkList

def make_message(feature):
   

    m = SR3Message()
    m['new_file'] = '/foo/bar/NewFile.txt'
    m['new_dir'] = '/foo/bar'
    m['geometry'] = features[feature]

    return m

def test___init__():
    options = sarracenia.config.default_config()
    options.logLevel = 'DEBUG'

    # Basic, happy path, without configured geometry
    geojson = sarracenia.flowcb.filter.geometry.Geometry(options)
    assert geojson.geometry_geojson == None
    assert geojson.o.geometry_maxDistance == -1


    # happy path with configured geometry
    options.geometry = [
        '{"type": "Polygon",',
        ' "coordinates": [',
        '    [',
        '        [-10.0, -10.0],',
        '        [10.0, -10.0],',
        '        [10.0, 10.0],',
        '        [-10.0, -10.0]',
        '    ]',
        ' ]',
        '}'
        ]
    options.geometry_maxDistance = 1.5
    geojson = sarracenia.flowcb.filter.geometry.Geometry(options)
    assert geojson.geometry_geojson['type'] == "Polygon"
    assert geojson.o.geometry_maxDistance == 1.5

    #unhappy path, with garbage geometry
    options.geometry = ['lkjasdf']
    with pytest.raises(json.decoder.JSONDecodeError):
        geojson = sarracenia.flowcb.filter.geometry.Geometry(options)


def test_after_accept():
    options = sarracenia.config.default_config()
    options.logLevel = 'DEBUG'

    # Testing when the config is a polygon
    options.geometry = [features['poly1']]
    geojson = sarracenia.flowcb.filter.geometry.Geometry(options)

    worklist = make_worklist()
    #accepted
    worklist.incoming.append(make_message("poly2"))
    worklist.incoming.append(make_message("pointA"))
    #rejected
    worklist.incoming.append(make_message("poly3"))
    worklist.incoming.append(make_message("pointB"))
    #failed
    worklist.incoming.append(make_message("line1"))

    geojson.after_accept(worklist)
    assert len(worklist.rejected) == 2
    assert len(worklist.incoming) == 2
    assert len(worklist.failed) == 1


    # testing when the config is a point
    options.geometry = [features['pointA']]
    options.geometry_maxDistance = 10
    geojson = sarracenia.flowcb.filter.geometry.Geometry(options)

    worklist = make_worklist()
    #accepted
    worklist.incoming.append(make_message("poly2"))
    worklist.incoming.append(make_message("pointA"))
    #rejected
    worklist.incoming.append(make_message("poly3"))
    worklist.incoming.append(make_message("pointB"))
    
    geojson.after_accept(worklist)
    assert len(worklist.rejected) == 2
    assert len(worklist.incoming) == 2

    
    #Testing what happens if a message has invalid geometry
    geojson = sarracenia.flowcb.filter.geometry.Geometry(options)

    worklist = make_worklist()
    #rejected
    worklist.incoming.append(make_message("pointC"))

    geojson.after_accept(worklist)
    assert len(worklist.failed) == 1
    

    #Tests for cases with missing maxDistance
    options.geometry_maxDistance = -1
    geojson = sarracenia.flowcb.filter.geometry.Geometry(options)

    worklist = make_worklist()
    #failed
    worklist.incoming.append(make_message("pointA"))
    worklist.incoming.append(make_message("pointB"))

    geojson.after_accept(worklist)
    assert len(worklist.failed) == 2


    #Tests where message geometry is invalid JSON
    geojson = sarracenia.flowcb.filter.geometry.Geometry(options)

    worklist = make_worklist()
    #failed
    worklist.incoming.append(make_message("pointB"))
    worklist.incoming[0]['geometry'] = 'lkjasdf'
    with pytest.raises(json.decoder.JSONDecodeError):
        geojson.after_accept(worklist)


    #Tests missing geometry in config
    del options.geometry
    geojson = sarracenia.flowcb.filter.geometry.Geometry(options)

    worklist = make_worklist()
    #rejected
    worklist.incoming.append(make_message("pointA"))
    worklist.incoming.append(make_message("pointB"))

    geojson.after_accept(worklist)
    assert len(worklist.rejected) == 2

