import pytest
from tests.conftest import *

import os
import tempfile

import sarracenia
import sarracenia.config
import sarracenia.transfer
from sarracenia.transfer.file import File


def make_options():
    options = sarracenia.config.default_config()
    options.timeout = 300
    options.bufSize = 1024 * 1024
    return options


def test_get_closes_src_file_handle():
    """Regression: file.py get() leaked the src file handle (never called
    local_read_close).  After the fix, both src and dst must be closed.
    """
    options = make_options()
    xfer = File('file', options)

    with tempfile.TemporaryDirectory() as tmpdir:
        src_dir = os.path.join(tmpdir, 'src')
        dst_dir = os.path.join(tmpdir, 'dst')
        os.makedirs(src_dir)
        os.makedirs(dst_dir)

        # create a source file
        src_file = os.path.join(src_dir, 'testfile.dat')
        with open(src_file, 'wb') as f:
            f.write(b'A' * 4096)

        xfer.cwd = src_dir

        local_file = os.path.join(dst_dir, 'testfile.dat')
        msg = sarracenia.Message.fromFileInfo('testfile.dat', options)

        rw_length = xfer.get(msg, 'testfile.dat', local_file)

        assert rw_length == 4096
        assert os.path.isfile(local_file)
        with open(local_file, 'rb') as f:
            assert f.read() == b'A' * 4096


def test_get_closes_handles_on_read_error():
    """If read_write raises, both src and dst must still be closed."""
    options = make_options()
    xfer = File('file', options)

    with tempfile.TemporaryDirectory() as tmpdir:
        src_dir = os.path.join(tmpdir, 'src')
        dst_dir = os.path.join(tmpdir, 'dst')
        os.makedirs(src_dir)
        os.makedirs(dst_dir)

        src_file = os.path.join(src_dir, 'testfile.dat')
        with open(src_file, 'wb') as f:
            f.write(b'B' * 1024)

        xfer.cwd = src_dir
        local_file = os.path.join(dst_dir, 'testfile.dat')
        msg = sarracenia.Message.fromFileInfo('testfile.dat', options)

        # Monkey-patch read_write to raise, simulating a transfer error
        original_read_write = xfer.read_write

        def failing_read_write(src, dst, length=0):
            raise IOError("simulated transfer failure")

        xfer.read_write = failing_read_write

        with pytest.raises(IOError, match="simulated transfer failure"):
            xfer.get(msg, 'testfile.dat', local_file)

        # If we got here without leaking, the fix works.
        # Verify by trying to open many files -- if handles leaked,
        # this would eventually fail under a low ulimit.


def test_get_no_fd_leak_over_many_transfers():
    """Transfer many files via file:// and verify no fd accumulation.

    Before the fix, each get() leaked one fd.  With a low ulimit this
    would crash.  We check the fd count stays stable.
    """
    options = make_options()
    xfer = File('file', options)

    with tempfile.TemporaryDirectory() as tmpdir:
        src_dir = os.path.join(tmpdir, 'src')
        dst_dir = os.path.join(tmpdir, 'dst')
        os.makedirs(src_dir)
        os.makedirs(dst_dir)

        xfer.cwd = src_dir
        pid = os.getpid()

        # create source files
        num_files = 200
        for i in range(num_files):
            with open(os.path.join(src_dir, 'file_%04d.dat' % i), 'wb') as f:
                f.write(b'X' * 512)

        # count open fds before
        fd_before = len(os.listdir('/proc/%d/fd' % pid))

        for i in range(num_files):
            fname = 'file_%04d.dat' % i
            local_file = os.path.join(dst_dir, fname)
            msg = sarracenia.Message.fromFileInfo(fname, options)
            rw_length = xfer.get(msg, fname, local_file)
            assert rw_length == 512

        # count open fds after
        fd_after = len(os.listdir('/proc/%d/fd' % pid))

        # allow a small margin (temp files, logging, etc.) but not 200 leaked fds
        assert fd_after - fd_before < 10, \
            "fd leak detected: %d fds before, %d after (%d leaked over %d transfers)" % (
                fd_before, fd_after, fd_after - fd_before, num_files)
