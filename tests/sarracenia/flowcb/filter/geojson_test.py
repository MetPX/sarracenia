import pytest
import types
import json
from tests.conftest import *
#from unittest.mock import Mock

import sarracenia.config
import sarracenia.flowcb.filter.geojson

from sarracenia import Message as SR3Message
import sarracenia.config

def make_worklist():
    WorkList = types.SimpleNamespace()
    WorkList.ok = []
    WorkList.incoming = []
    WorkList.rejected = []
    WorkList.failed = []
    WorkList.directories_ok = []
    return WorkList

def make_message():
    m = SR3Message()
    m['new_file'] = '/foo/bar/NewFile.txt'
    m['new_dir'] = '/foo/bar'

    return m

def test___init__():
    options = sarracenia.config.default_config()
    options.logLevel = 'DEBUG'

    # Basic, happy path, without configured geometry
    geojson = sarracenia.flowcb.filter.geojson.GeoJSON(options)
    assert geojson.geometry_geojson == None


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
    geojson = sarracenia.flowcb.filter.geojson.GeoJSON(options)
    assert geojson.geometry_geojson['type'] == "Polygon"

    #unhappy path, with garbage geometry
    options.geometry = ['lkjasdf']
    with pytest.raises(json.decoder.JSONDecodeError):
        geojson = sarracenia.flowcb.filter.geojson.GeoJSON(options)