import pytest
from tests.conftest import *
from unittest.mock import patch, MagicMock

import types

import sarracenia
import sarracenia.flowcb
from sarracenia.flow import Flow


def make_flow():
    """Create a minimal Flow instance with patched-out plugin loading."""
    cfg = MagicMock()
    cfg.logLevel = 'INFO'
    cfg.logFormat = '%(asctime)s [%(levelname)s] %(message)s'
    cfg.settings = {}
    cfg.topicPrefix = ['v03']
    cfg.post_topicPrefix = ['v03']
    cfg.nodupe_ttl = 0
    cfg.nodupe_driver = 'disk'
    cfg.plugins_early = []
    cfg.plugins_late = []
    cfg.component = 'flow'
    cfg.config = 'test'
    cfg.no = 1
    cfg.novipFilename = '/tmp/test_flow_close_novip'

    flow = Flow.__new__(Flow)
    flow._stop_requested = False
    flow.o = cfg

    flow.plugins = {}
    for ep in sarracenia.flowcb.entry_points:
        flow.plugins[ep] = []

    flow.worklist = types.SimpleNamespace()
    flow.worklist.ok = []
    flow.worklist.incoming = []
    flow.worklist.rejected = []
    flow.worklist.failed = []
    flow.worklist.directories_ok = []

    flow._logLevel_debug = False
    flow.proto = {}
    return flow


def test_close__closes_proto_connections():
    """close() should close all active proto connections."""
    flow = make_flow()

    mock_sftp = MagicMock()
    mock_ftp = MagicMock()
    flow.proto = {'sftp': mock_sftp, 'ftp': mock_ftp}

    with patch('os.path.exists', return_value=False):
        flow.close()

    mock_sftp.close.assert_called_once()
    mock_ftp.close.assert_called_once()
    assert flow.proto['sftp'] is None
    assert flow.proto['ftp'] is None


def test_close__skips_none_proto():
    """close() should skip proto entries that are already None."""
    flow = make_flow()

    mock_sftp = MagicMock()
    flow.proto = {'sftp': mock_sftp, 'ftp': None}

    with patch('os.path.exists', return_value=False):
        flow.close()

    mock_sftp.close.assert_called_once()
    assert flow.proto['sftp'] is None
    assert flow.proto['ftp'] is None


def test_close__proto_close_exception_doesnt_crash():
    """If a proto.close() raises, close() should continue with others."""
    flow = make_flow()

    mock_sftp = MagicMock()
    mock_sftp.close.side_effect = OSError("connection reset")
    mock_ftp = MagicMock()
    flow.proto = {'sftp': mock_sftp, 'ftp': mock_ftp}

    with patch('os.path.exists', return_value=False):
        flow.close()

    mock_sftp.close.assert_called_once()
    mock_ftp.close.assert_called_once()
    assert flow.proto['sftp'] is None
    assert flow.proto['ftp'] is None


def test_close__empty_proto():
    """close() should work fine with no proto connections."""
    flow = make_flow()
    flow.proto = {}

    with patch('os.path.exists', return_value=False):
        flow.close()

    assert flow.proto == {}
