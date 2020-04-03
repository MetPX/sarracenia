""" This file is part of metpx-sarracenia.

metpx-sarracenia
Documentation: https://github.com/MetPX/sarracenia

sr_config_unit_test.py : test utility tool used for sr_config


Code contributed by:
 Benoit Lapointe - Shared Services Canada
"""
import tempfile
import unittest

try:
    from sr_cache import *
    from sr_config import *
except ImportError:
    from sarra.sr_cache import *
    from sarra.sr_config import *


class SrCacheTestCase(unittest.TestCase):
    """ The parent class of all sr_cache test cases

    It handles base configs used in all tests
    """
    def setUp(self) -> None:
        # creating a temporary cache directory/file
        self.tmpdirname = tempfile.TemporaryDirectory().name
        if not os.path.exists(self.tmpdirname):
            os.mkdir(self.tmpdirname)
        self.tmppath = os.path.join(self.tmpdirname, 'cache_test_file')

        self.cfg = sr_config()
        self.cfg.config_name = "test"
        self.cfg.configure()

        self.cfg.option("caching 1".split())

        # check creation addition close
        self.cache = sr_cache(self.cfg)
        self.cache.open(self.tmppath)

    def tearDown(self) -> None:
        self.cache.clean()
        self.cache.close(unlink=True)
        os.removedirs(self.tmpdirname)

    def test_collision_w_2_entries(self):
        self.cache.check('key1', 'file1', 'part1')
        self.cache.check('key2', 'file2', 'part2')
        self.cache.check('key1', 'file1', 'part1')
        self.cache.load()
        # one collision when adding so 2 entries
        self.assertEqual(2, len(self.cache.cache_dict), "test 01: expecting 2 entries...")

    def test_check_expire(self):
        self.test_collision_w_2_entries()
        # expire previous and add 3
        time.sleep(1)
        self.cache.check('key3', 'file3', 'part3')
        self.cache.check_expire()
        self.cache.check('key4', 'file4', None)
        self.cache.check('key5', 'file5', 'part5')
        self.assertEqual(3, len(self.cache.cache_dict), "test 02: expecting 3 entries...")

        # checking cache internals ...
        # print("%s" % cache.cache_dict)

    def test_zero_entry(self):
        # expire previous
        self.assertEqual(0, len(self.cache.cache_dict), "test 03: expecting 0 entry...")

    def test_hundred_entry(self):
        # add 100 entries
        self.cache.load()
        i = 0
        while i < 100:
            self.cache.check('key%d' % i, 'file%d' % i, 'part%d' % i)
            i = i + 1
        self.assertEqual(100, len(self.cache.cache_dict), "test 04: expecting 100 entries...")

    def test_zero_entry_free_cache(self):
        # free cache
        self.cache.free()
        self.assertEqual(0, len(self.cache.cache_dict), "test 05: expecting 0 entry...")

    def test_delete_entry(self):
        # add 10 entries
        i = 0
        while i < 10:
            self.cache.check('key%d' % i, 'file%d' % i, 'part%d' % i)
            self.cache.check('key%d' % i, 'file%d' % i, 'part0%d' % i)
            self.cache.check('key%d' % i, 'file%d' % i, 'part1%d' % i)
            self.cache.check('key%d' % i, 'file%d' % i, 'part2%d' % i)
            i = i + 1
        # delete one
        self.cache.delete_path('file8')
        self.assertEqual(9, len(self.cache.cache_dict),
                         "test 06: expecting 9 entries...got %d" % len(self.cache.cache_dict))
        # expire and clean
        time.sleep(1)
        self.cache.clean()
        self.assertEqual(0, len(self.cache.cache_dict), "test 07: expecting 0 entry...")

    def test_save_entry(self):
        # add one and save
        self.cache.check('key%d' % 0, 'file%d' % 0, 'part2%d' % 0)
        self.cache.save()
        self.assertEqual(1, len(self.cache.cache_dict), "test 08: expecting 1 entry...")

    def test_tmppath_exist(self):
        self.assertTrue(os.path.exists(self.tmppath), "test 09: cache file should exists")

    def test_tmppath_not_exist(self):
        # close and unlink
        self.cache.close(unlink=True)
        self.assertFalse(os.path.exists(self.tmppath), "test 10: cache file should have been deleted")


# ===================================
# MAIN
# ===================================

def suite():
    """ Create the test suite that include all sr_config test cases

    :return: sr_config test suite
    """
    sr_config_suite = unittest.TestSuite()
    sr_config_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(SrCacheTestCase))
    return sr_config_suite


if __name__ == 'main':
    runner = unittest.TextTestRunner()
    runner.run(suite())
