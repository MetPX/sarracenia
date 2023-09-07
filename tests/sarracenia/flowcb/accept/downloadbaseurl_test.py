import pytest
import types

import os

#useful for debugging tests
def pretty(*things, **named_things):
    import pprint
    for t in things:
        pprint.PrettyPrinter(indent=2, width=200).pprint(t)
    for k,v in named_things.items():
        print(str(k) + ":")
        pprint.PrettyPrinter(indent=2, width=200).pprint(v)

from sarracenia.flowcb.accept.downloadbaseurl import DownloadBaseUrl
from sarracenia import Message as SR3Message
import sarracenia.config

def make_message(fileNumber = 1):
    m = SR3Message()
    m['baseUrl'] = 'http://NotAReal.url/a/rel/Path/file.txt'
    m['new_file'] = f"/file{fileNumber}.txt"

    return m

def make_worklist():
    WorkList = types.SimpleNamespace()
    WorkList.ok = []
    WorkList.incoming = []
    WorkList.rejected = []
    WorkList.failed = []
    WorkList.directories_ok = []
    return WorkList

def test___init__():
    options = sarracenia.config.default_config()
    downloadbaseurl = DownloadBaseUrl(options)


def test_after_accept(tmp_path, mocker):
    import io
    mocker.patch('urllib.request.urlopen', return_value=io.BytesIO(b'SomeRandomData'))

    new_dir = str(tmp_path) + os.sep + 'new_dir'
    options = sarracenia.config.default_config()
    options.new_dir = new_dir
    downloadbaseurl = DownloadBaseUrl(options)

    #Set 1 - option.new_dir doesn't exists
    worklist = make_worklist()
    worklist.incoming = [make_message(1)]
    downloadbaseurl.after_accept(worklist)
    assert len(worklist.incoming) == 1
    assert open(new_dir + '/file1.txt', 'r').read() == "SomeRandomData"