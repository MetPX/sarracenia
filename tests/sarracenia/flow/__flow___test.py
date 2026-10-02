import pytest
from tests.conftest import *

import sarracenia.config
import sarracenia.flow
import copy

__COMPONENT="subscribe"
__CONFIG="flow_class_test"

def __make_fake_config(lines=[]):
    """ build and return a fake config object
    """
    options = copy.deepcopy(sarracenia.config.default_config())
    options.component = __COMPONENT
    options.config = __CONFIG
    options.action = 'start'
    for line in lines:
        options.parse_line(__COMPONENT, __CONFIG, f"{__COMPONENT}/{__CONFIG}", 1, line)
    options.metricsFilename = '/tmp/fake_filename_nothing_here'
    options.novipFilename = options.metricsFilename
    options.acceptUnmatched = False
    options.finalize()
    return options


def test_msg_accepted_with_sundew_extension():
    """
    Regression test for https://github.com/MetPX/sarracenia/issues/1573
    sundew_extension should be included in filtering, even when URL has a port
    """
    options = __make_fake_config(lines=["accept .*rxer:CCCC:TT:3:Direct.*"])

    flow = sarracenia.flow.Flow(options)
    flow.have_vip = True
    msg = sarracenia.Message()
    msg['pubTime'] = '20260101T010203.123'
    msg['baseUrl'] = 'http://dms-dev1.domain:8180/data/msc/'
    msg['relPath'] = 'forecast/atmospheric/aviation/file.txt'
    msg['sundew_extension'] = 'rxer:CCCC:TT:3:Direct'

    flow.worklist.incoming.append(msg)

    # based on the accept statement, the message should only be accepted when the sundew_extension is correctly added
    flow.filter()
    assert(len(flow.worklist.rejected) == 0)
    assert(msg not in flow.worklist.rejected)
    assert(msg in flow.worklist.incoming)

def test_msg_rejected_when_sundew_extension_already_present():
    """
    If the path itself already contains a different sundew extension,
    the sundew_extension header in the msg should not be used for filtering
    """
    options = __make_fake_config(lines=["accept .*rxer:CCCC:TT:3:Direct.*"])

    flow = sarracenia.flow.Flow(options)
    flow.have_vip = True
    msg = sarracenia.Message()
    msg['pubTime'] = '20260101T010203.123'
    msg['baseUrl'] = 'http://dms-dev1.domain:8180/data/msc/'
    msg['relPath'] = 'forecast/atmospheric/aviation/file.txt:something:CWAO:SA:3:Direct'
    msg['sundew_extension'] = 'rxer:CCCC:TT:3:Direct'

    flow.worklist.incoming.append(msg)

    # msg already has a different sundew extension that does not match the accept, it should be rejected
    flow.filter()

    # worklist.rejected gets acked and set to [] at the end of filter
    assert len(flow.worklist.incoming) == 0
    assert len(flow.worklist.rejected) == 0
    assert msg not in flow.worklist.incoming


def test_sender_dry_run_with_different_cwd_and_inflight():
    """
    Regression test for https://github.com/robjarawan/sarracenia/issues/137
    Flow.send with dry_run True must work when process cwd != local_dir,
    must not mutate cwd or perform remote i/o, and must handle all inflight modes.
    """
    import tempfile
    import os
    import sarracenia.transfer
    from sarracenia.flow.sender import Sender

    class DummyTransfer:
        def __init__(self, proto, options):
            self.proto = proto
            self.o = options

        def check_is_connected(self):
            return True

        def seek(self, *args, **kwargs):
            raise AssertionError("seek should not be called in dry_run")

        def rename(self, *args, **kwargs):
            raise AssertionError("rename should not be called in dry_run")

        def umask(self, *args, **kwargs):
            raise AssertionError("umask should not be called in dry_run")

        def cd_forced(self, *args, **kwargs):
            raise AssertionError("cd_forced should not be called in dry_run")

        def put(self, *args, **kwargs):
            raise AssertionError("put should not be called in dry_run")

        def putAccelerated(self, *args, **kwargs):
            raise AssertionError("putAccelerated should not be called in dry_run")

        def close(self):
            pass

    orig_cwd = os.getcwd()
    orig_factory = sarracenia.transfer.Transfer.factory
    sarracenia.transfer.Transfer.factory = staticmethod(lambda proto, opts: DummyTransfer(proto, opts))
    try:
        with tempfile.TemporaryDirectory() as td:
            base_dir = os.path.join(td, 'local_base')
            os.makedirs(base_dir)
            file_path = os.path.join(base_dir, 'sample.txt')
            test_content = b'test dry run payload'
            with open(file_path, 'wb') as f:
                f.write(test_content)

            dest_dir = os.path.join(td, 'dest')
            os.makedirs(dest_dir)

            for inflight_val in [None, '.', '.tmp', 'umask', 'dest_sub/', '.hidden/', '/absolute']:
                options = copy.deepcopy(sarracenia.config.default_config())
                options.component = 'sender'
                options.config = 'test_sender_dry_run'
                options.action = 'start'
                options.parse_line(
                    'sender', 'test_sender_dry_run', 'sender/test_sender_dry_run', 1, f'baseDir {base_dir}')
                options.parse_line(
                    'sender', 'test_sender_dry_run', 'sender/test_sender_dry_run', 2, f'sendTo file://{dest_dir}')
                options.parse_line(
                    'sender', 'test_sender_dry_run', 'sender/test_sender_dry_run', 3, 'dry_run True')
                if inflight_val is not None:
                    options.parse_line(
                        'sender', 'test_sender_dry_run', 'sender/test_sender_dry_run', 4, f'inflight {inflight_val}')
                else:
                    options.parse_line(
                        'sender', 'test_sender_dry_run', 'sender/test_sender_dry_run', 4, 'inflight None')
                options.metricsFilename = os.path.join(td, 'metrics')
                options.novipFilename = options.metricsFilename
                options.acceptUnmatched = False
                options.finalize()

                sender = Sender(options)
                msg = sarracenia.Message()
                msg['relPath'] = 'sample.txt'
                msg['new_dir'] = dest_dir
                msg['new_file'] = 'sample.txt'
                msg['local_offset'] = 0

                # Ensure process cwd is outside base_dir
                os.chdir(td)
                assert os.getcwd() != base_dir
                cwd_before = os.getcwd()

                ret = sender.send(msg, options)
                assert ret > 0, f"send failed for inflight={inflight_val}"
                assert msg['report']['code'] == 201
                assert sender.metrics['flow']['transferTxFiles'] >= 1
                assert sender.metrics['flow']['transferTxBytes'] >= len(test_content)
                assert os.getcwd() == cwd_before
                assert os.listdir(dest_dir) == []

            # Inplace block transfer branch test
            inplace_options = copy.deepcopy(options)
            inplace_options.inflight = '.'
            inplace_sender = Sender(inplace_options)
            inplace_msg = sarracenia.Message()
            inplace_msg['relPath'] = 'sample.txt'
            inplace_msg['new_dir'] = dest_dir
            inplace_msg['new_file'] = 'sample.txt'
            inplace_msg['local_offset'] = 0
            inplace_msg['offset'] = 0
            inplace_msg['size'] = len(test_content)
            inplace_msg['blocks'] = {'method': 'inplace', 'size': len(test_content)}
            os.chdir(td)
            cwd_before = os.getcwd()
            ret = inplace_sender.send(inplace_msg, inplace_options)
            assert ret > 0
            assert inplace_msg['report']['code'] == 201
            assert os.getcwd() == cwd_before
            assert os.listdir(dest_dir) == []

            # Negative test: missing local file returns 0
            missing_msg = sarracenia.Message()
            missing_msg['relPath'] = 'nonexistent.txt'
            missing_msg['new_dir'] = dest_dir
            missing_msg['new_file'] = 'nonexistent.txt'
            missing_msg['local_offset'] = 0
            os.chdir(td)
            cwd_before = os.getcwd()
            ret = sender.send(missing_msg, options)
            assert ret == 0
            assert os.getcwd() == cwd_before

            # Negative test: unsupported inflight returns -1
            invalid_options = copy.deepcopy(options)
            invalid_options.inflight = 'unsupported_mode'
            invalid_sender = Sender(invalid_options)
            valid_msg = sarracenia.Message()
            valid_msg['relPath'] = 'sample.txt'
            valid_msg['new_dir'] = dest_dir
            valid_msg['new_file'] = 'sample.txt'
            valid_msg['local_offset'] = 0
            ret = invalid_sender.send(valid_msg, invalid_options)
            assert ret == -1

            # Negative test: empty inflight string returns -1 without IndexError
            empty_options = copy.deepcopy(options)
            empty_options.inflight = ''
            empty_sender = Sender(empty_options)
            ret = empty_sender.send(valid_msg, empty_options)
            assert ret == -1

            # Negative test: non-string numeric inflight interval returns -1
            numeric_options = copy.deepcopy(options)
            numeric_options.inflight = 300
            numeric_sender = Sender(numeric_options)
            ret = numeric_sender.send(valid_msg, numeric_options)
            assert ret == -1

            # Negative test: path traversal escaping baseDir returns -1
            traversal_msg = sarracenia.Message()
            traversal_msg['relPath'] = '../../etc/passwd'
            traversal_msg['new_dir'] = dest_dir
            traversal_msg['new_file'] = 'passwd'
            traversal_msg['local_offset'] = 0
            ret = sender.send(traversal_msg, options)
            assert ret == -1

            # Negative test: inplace block without seek capability in dry_run returns -1
            noseek_options = copy.deepcopy(options)

            class NoSeekDummyTransfer:
                def __init__(self, proto, options):
                    pass

                def check_is_connected(self):
                    return True

                def connect(self):
                    return True

                def cd_forced(self, path):
                    pass

            sarracenia.transfer.Transfer.factory = staticmethod(lambda proto, opts: NoSeekDummyTransfer(proto, opts))
            noseek_sender = Sender(noseek_options)
            inplace_fail_msg = sarracenia.Message()
            inplace_fail_msg['relPath'] = 'sample.txt'
            inplace_fail_msg['new_dir'] = dest_dir
            inplace_fail_msg['new_file'] = 'sample.txt'
            inplace_fail_msg['blocks'] = {'method': 'inplace', 'size': 100}
            ret = noseek_sender.send(inplace_fail_msg, noseek_options)
            assert ret == -1
            sarracenia.transfer.Transfer.factory = orig_factory
    finally:
        sarracenia.transfer.Transfer.factory = orig_factory
        os.chdir(orig_cwd)


def test_sender_live_inflight_and_error_handling():
    """
    Test live sender transfer execution across inflight modes, verifying temporary
    paths, rename operations, process CWD restoration, and rejection of negative
    or partial write results.
    """
    import tempfile
    import os
    import sarracenia.transfer
    from sarracenia.flow.sender import Sender

    class RecordingTransfer:
        def __init__(self, proto, options):
            self.proto = proto
            self.o = options
            self.put_calls = []
            self.rename_calls = []
            self.cd_forced_calls = []
            self.put_result = None

        def check_is_connected(self):
            return True

        def connect(self):
            return True

        def cd_forced(self, path):
            self.cd_forced_calls.append(path)

        def rename(self, old_path, new_path):
            self.rename_calls.append((old_path, new_path))

        def put(self, msg, local_file, remote_file, *args):
            if args:
                self.put_calls.append((local_file, remote_file, *args))
            else:
                self.put_calls.append((local_file, remote_file))
            if self.put_result is not None:
                return self.put_result
            return msg['size']

        def seek(self, offset):
            pass

        def close(self):
            pass

    class NoRenameTransfer:
        def __init__(self, proto, options):
            self.proto = proto
            self.o = options
            self.put_calls = []

        def check_is_connected(self):
            return True

        def connect(self):
            return True

        def put(self, msg, local_file, remote_file, *args):
            self.put_calls.append((local_file, remote_file))
            return msg['size']

        def close(self):
            pass

    orig_cwd = os.getcwd()
    orig_factory = sarracenia.transfer.Transfer.factory
    active_transfer = [None]
    sarracenia.transfer.Transfer.factory = staticmethod(lambda proto, opts: active_transfer[0])

    try:
        with tempfile.TemporaryDirectory() as td:
            base_dir = os.path.join(td, 'local_base')
            os.makedirs(base_dir)
            file_path = os.path.join(base_dir, 'sample.txt')
            test_content = b'sample test data payload'
            with open(file_path, 'wb') as f:
                f.write(test_content)

            dest_dir = os.path.join(td, 'dest')
            os.makedirs(dest_dir)

            test_cases = [
                ('.', '.sample.txt'),
                ('.tmp', 'sample.txt.tmp'),
                ('dest_sub/', 'dest_sub/sample.txt'),
                ('.hidden/', '.hidden/sample.txt'),
                ('/absolute', '/absolute/sample.txt'),
            ]

            for inflight_val, expected_tmp in test_cases:
                options = copy.deepcopy(sarracenia.config.default_config())
                options.component = 'sender'
                options.config = 'test_live_sender'
                options.action = 'start'
                options.parse_line('sender', 'test_live_sender', 'sender/test', 1, f'baseDir {base_dir}')
                options.parse_line('sender', 'test_live_sender', 'sender/test', 2, f'sendTo file://{dest_dir}')
                options.parse_line('sender', 'test_live_sender', 'sender/test', 3, f'inflight {inflight_val}')
                options.metricsFilename = os.path.join(td, 'metrics')
                options.novipFilename = options.metricsFilename
                options.acceptUnmatched = False
                options.finalize()

                rec = RecordingTransfer('file', options)
                active_transfer[0] = rec
                sender = Sender(options)
                msg = sarracenia.Message()
                msg['relPath'] = 'sample.txt'
                msg['new_dir'] = dest_dir
                msg['new_file'] = 'sample.txt'
                msg['local_offset'] = 0

                os.chdir(td)
                cwd_before = os.getcwd()

                ret = sender.send(msg, options)
                assert ret == 1
                assert rec.put_calls == [('sample.txt', expected_tmp)]
                assert rec.rename_calls == [(expected_tmp, 'sample.txt')]
                assert msg['report']['code'] == 201
                assert sender.metrics['flow']['transferTxFiles'] == 1
                assert sender.metrics['flow']['transferTxBytes'] == len(test_content)
                assert os.getcwd() == cwd_before
                if inflight_val == 'dest_sub/':
                    assert rec.cd_forced_calls == [dest_dir, os.path.join(dest_dir, 'dest_sub'), dest_dir]
                elif inflight_val == '/absolute':
                    assert rec.cd_forced_calls == [dest_dir, '/absolute', dest_dir]

            # Inplace block transfer with inflight=None verifies offsets and method precedence
            inplace_options = copy.deepcopy(options)
            inplace_options.inflight = None
            inplace_rec = RecordingTransfer('file', inplace_options)
            active_transfer[0] = inplace_rec
            inplace_sender = Sender(inplace_options)
            inplace_msg = sarracenia.Message()
            inplace_msg['relPath'] = 'sample.txt'
            inplace_msg['new_dir'] = dest_dir
            inplace_msg['new_file'] = 'sample.txt'
            inplace_msg['local_offset'] = 50
            inplace_msg['offset'] = 100
            inplace_msg['size'] = 20
            inplace_msg['blocks'] = {'method': 'inplace', 'size': 100}
            ret = inplace_sender.send(inplace_msg, inplace_options)
            assert ret == 1
            assert inplace_rec.put_calls == [('sample.txt', 'sample.txt', 100, 100, 20)]
            assert inplace_rec.rename_calls == []
            assert inplace_msg['report']['code'] == 201

            # Native SR3 block transfer with manifest and block number
            native_rec = RecordingTransfer('file', inplace_options)
            active_transfer[0] = native_rec
            native_sender = Sender(inplace_options)
            native_msg = sarracenia.Message()
            native_msg['relPath'] = 'sample.txt'
            native_msg['new_dir'] = dest_dir
            native_msg['new_file'] = 'sample.txt'
            native_msg['size'] = 14
            native_msg['blocks'] = {
                'method': 'inplace',
                'number': 1,
                'manifest': {
                    0: {'size': 10},
                    1: {'size': 14}
                }
            }
            ret = native_sender.send(native_msg, inplace_options)
            assert ret == 1
            assert native_rec.put_calls == [('sample.txt', 'sample.txt', 10, 10, 14)]
            assert native_rec.rename_calls == []
            assert native_msg['report']['code'] == 201

            # Inplace short final block (msg['size'] < blocks['size']) succeeds
            short_rec = RecordingTransfer('file', inplace_options)
            active_transfer[0] = short_rec
            short_sender = Sender(inplace_options)
            short_msg = sarracenia.Message()
            short_msg['relPath'] = 'sample.txt'
            short_msg['new_dir'] = dest_dir
            short_msg['new_file'] = 'sample.txt'
            short_msg['local_offset'] = 0
            short_msg['offset'] = 500
            short_msg['size'] = 20
            short_msg['blocks'] = {'method': 'inplace', 'size': 100}
            ret = short_sender.send(short_msg, inplace_options)
            assert ret == 1
            assert short_msg['report']['code'] == 201

            # Partitioned block transfer uploads directly to new_file without rename
            part_options = copy.deepcopy(options)
            part_options.inflight = '.tmp'
            part_rec = RecordingTransfer('file', part_options)
            active_transfer[0] = part_rec
            part_sender = Sender(part_options)
            part_msg = sarracenia.Message()
            part_msg['relPath'] = 'sample.txt'
            part_msg['new_dir'] = dest_dir
            part_msg['new_file'] = 'sample.txt'
            part_msg['local_offset'] = 0
            part_msg['size'] = 20
            part_msg['blocks'] = {'method': 'append', 'size': 100}
            ret = part_sender.send(part_msg, part_options)
            assert ret == 1
            assert part_rec.put_calls == [('sample.txt', 'sample.txt')]
            assert part_rec.rename_calls == []
            assert part_msg['report']['code'] == 201

            # Negative test: put() returns -1 (e.g. S3 / Azure transfer failure)
            rec = RecordingTransfer('file', options)
            rec.put_result = -1
            active_transfer[0] = rec
            sender = Sender(options)
            fail_msg = sarracenia.Message()
            fail_msg['relPath'] = 'sample.txt'
            fail_msg['new_dir'] = dest_dir
            fail_msg['new_file'] = 'sample.txt'
            fail_msg['local_offset'] = 0
            ret = sender.send(fail_msg, options)
            assert ret == 0
            assert rec.rename_calls == []
            assert 'report' not in fail_msg or fail_msg['report']['code'] != 201

            # Negative test: put() writes partial bytes
            rec = RecordingTransfer('file', options)
            rec.put_result = len(test_content) // 2
            active_transfer[0] = rec
            sender = Sender(options)
            partial_msg = sarracenia.Message()
            partial_msg['relPath'] = 'sample.txt'
            partial_msg['new_dir'] = dest_dir
            partial_msg['new_file'] = 'sample.txt'
            partial_msg['local_offset'] = 0
            ret = sender.send(partial_msg, options)
            assert ret == 0
            assert rec.rename_calls == []
            assert 'report' not in partial_msg or partial_msg['report']['code'] != 201

            # Negative test: backend lacking rename when inflight requires rename
            no_rename_rec = NoRenameTransfer('file', options)
            active_transfer[0] = no_rename_rec
            sender = Sender(options)
            no_ren_msg = sarracenia.Message()
            no_ren_msg['relPath'] = 'sample.txt'
            no_ren_msg['new_dir'] = dest_dir
            no_ren_msg['new_file'] = 'sample.txt'
            no_ren_msg['local_offset'] = 0
            ret = sender.send(no_ren_msg, options)
            assert ret == -1
            assert no_rename_rec.put_calls == []

            # Negative test: staging directory equals destination directory returns -1
            alias_options = copy.deepcopy(options)
            alias_options.inflight = './'
            alias_rec = RecordingTransfer('file', alias_options)
            active_transfer[0] = alias_rec
            alias_sender = Sender(alias_options)
            alias_msg = sarracenia.Message()
            alias_msg['relPath'] = 'sample.txt'
            alias_msg['new_dir'] = dest_dir
            alias_msg['new_file'] = 'sample.txt'
            alias_msg['local_offset'] = 0
            ret = alias_sender.send(alias_msg, alias_options)
            assert ret == -1

            # Negative test: absolute inflight path on S3 returns -1
            s3_options = copy.deepcopy(options)
            s3_options.inflight = '/absolute'
            s3_options.sendTo = 's3://bucket/dest'
            s3_rec = RecordingTransfer('s3', s3_options)
            active_transfer[0] = s3_rec
            s3_sender = Sender(s3_options)
            s3_msg = sarracenia.Message()
            s3_msg['relPath'] = 'sample.txt'
            s3_msg['new_dir'] = 'dest'
            s3_msg['new_file'] = 'sample.txt'
            s3_msg['local_offset'] = 0
            ret = s3_sender.send(s3_msg, s3_options)
            assert ret == -1

            # Test fileOp symlink metadata creation succeeds even if target points outside baseDir
            link_msg = sarracenia.Message()
            link_msg['relPath'] = 'symlink_test'
            link_msg['new_dir'] = dest_dir
            link_msg['new_file'] = 'symlink_test'
            link_msg['fileOp'] = {'link': '/outside/absolute/target'}
            link_rec = RecordingTransfer('file', options)
            link_rec.symlink_calls = []
            link_rec.symlink = lambda target, linkname: link_rec.symlink_calls.append((target, linkname))
            active_transfer[0] = link_rec
            link_sender = Sender(options)
            ret = link_sender.send(link_msg, options)
            assert ret == 1
            assert link_rec.symlink_calls == [('/outside/absolute/target', 'symlink_test')]
    finally:
        sarracenia.transfer.Transfer.factory = orig_factory
        os.chdir(orig_cwd)
