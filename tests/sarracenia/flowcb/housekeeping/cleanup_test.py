import os
import time
import sarracenia.config

from sarracenia.flowcb.housekeeping.cleanup import Cleanup

def make_cleanup(path, cleanup_age):
    options = sarracenia.config.Config()
    options.logLevel = 'info'
    options.cleanup_age = cleanup_age
    options.postpath = [str(path)]
    
    return Cleanup(options)


def test_cleanup_age_parses_duration():
    options = sarracenia.config.Config()
    options.parse_line('watch', 'cleanup', 'watch/cleanup.conf', 1, 'cleanup_age 2h')

    assert options.cleanup_age == 7200


def test_cleanup_removes_old_files_recursively_but_keeps_recent_files(tmp_path):
    nested = tmp_path / 'nested'
    nested.mkdir()
    old_file = nested / 'old.dat'
    recent_file = tmp_path / 'recent.dat'
    old_file.write_text('old')
    recent_file.write_text('recent')
    old_time = time.time() - 120
    os.utime(old_file, (old_time, old_time))

    make_cleanup(tmp_path, 60).on_housekeeping()

    assert not old_file.exists()
    assert recent_file.exists()


def test_cleanup_age_zero_disables_deletion(tmp_path):
    old_file = tmp_path / 'old.dat'
    old_file.write_text('old')
    old_time = time.time() - 120
    os.utime(old_file, (old_time, old_time))

    make_cleanup(tmp_path, 0).on_housekeeping()

    assert old_file.exists()