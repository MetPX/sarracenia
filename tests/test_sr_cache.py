""" This file is part of metpx-sarracenia.

metpx-sarracenia
Documentation: https://github.com/MetPX/sarracenia

test_sr_cache.py : test utility tool used for sr_cache

TODO Documents what it does (and doesn't):
  - This modules test sr_cache in the smallest possible unit,
  - dependencies-free, uses Mock to prune it out https://docs.python.org/3/library/unittest.mock.html in the simplest
  possible way
  - in per-method defined cases, trying to acheive a 100% test coverage
  - basically each case is defined by 3 steps: prepare, execute, evaluate
    + evaluation may split in 2 when cases are getting more complex (final state & intermediate calls)

Code contributed by:
 Benoit Lapointe - Shared Services Canada
"""
import logging
import os
import time
import unittest
from enum import Enum, auto
from unittest import TestCase
from unittest.mock import patch, call, Mock, DEFAULT

from sarra.sr_cache import sr_cache

KEY_FMT = "{}_{}"
ENTRY_KEY_FMT = "{}*{}"

ASSERT_INVALID_RETURNED_VALUE_FMT = "{} returned a misleading value"
ASSERT_INVALID_VALUE_FMT = "{} is invalid"
ASSERT_MOCK_CALLS = 'external call(s) differ'
WRITE_LINE_FMT = "{} {:f} {} {}\n"


class SrCacheCase(TestCase):
    def setUp(self) -> None:
        self.now = time.time()
        self.file = f"{__class__.__name__}.file"
        self.part = 'p,457,2,24,1'
        self.entry_key = ENTRY_KEY_FMT.format(self.file, self.part)
        self.cache_entry = {self.entry_key: self.now}
        self.path = os.path.join(__class__.__name__, self.file)

        self.logger = logging.getLogger(__class__.__name__)
        self.cache_basis = CacheBasis.name.name
        self.caching = 10
        self.cache = sr_cache(self)
        self.cache.cache_file = f"{__class__.__name__}.cache"
        self.count = self.cache.count

    @patch('_io.TextIOWrapper')
    @patch('sarra.sr_cache.nowflt')
    def test_check__checksum_new(self, nowflt, fp):
        # Prepare test
        self.key = self.test_check__checksum_new.__name__
        nowflt.return_value = self.now
        self.cache.fp = fp
        # Execute test
        result = self.cache.check(self.key, self.path, self.part)

        # Evaluate internal state (attributes values)
        self.assertIsNone(self.cache.cache_hit, ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_hit'))
        self.assertTrue(result, ASSERT_INVALID_RETURNED_VALUE_FMT.format('sr_cache.check'))
        expected = {self.key: self.cache_entry}
        assert_msg = ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_dict')
        self.assertDictEqual(expected, self.cache.cache_dict, assert_msg)
        assert_msg = ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache.count')
        self.assertEqual(self.count + 1, self.cache.count, assert_msg)

        # Evaluate external calls
        expected = [call.write(WRITE_LINE_FMT.format(self.key, nowflt.return_value, self.file, self.part))]
        self.assertEqual(expected, fp.mock_calls, ASSERT_MOCK_CALLS)

    @patch('_io.TextIOWrapper')
    @patch('sarra.sr_cache.nowflt')
    def test_check__checksum_same__value_same__cache_hit(self, nowflt, fp):
        # Prepare test
        self.key = self.test_check__checksum_same__value_same__cache_hit.__name__
        nowflt.return_value = self.now + 1
        self.cache.fp = fp
        self.cache.cache_dict[self.key] = self.cache_entry
        self.cache.count += 1
        # Execute test
        result = self.cache.check(self.key, self.path, self.part)

        # Evaluate internal state (attributes values)
        self.assertFalse(result, ASSERT_INVALID_RETURNED_VALUE_FMT.format('sr_cache.check'))
        assert_msg = ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_hit')
        self.assertEqual(self.cache_entry.popitem()[0], self.cache.cache_hit, assert_msg)
        expected = {self.key: self.cache_entry}
        self.assertDictEqual(expected, self.cache.cache_dict, ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_dict'))
        self.assertEqual(self.count + 2, self.cache.count, ASSERT_INVALID_VALUE_FMT.format('sr_cache.count'))

        # Evaluate external calls
        expected = [call.write(WRITE_LINE_FMT.format(self.key, nowflt.return_value, self.file, self.part))]
        self.assertEqual(expected, fp.mock_calls, ASSERT_MOCK_CALLS)

    @patch('_io.TextIOWrapper')
    @patch('sarra.sr_cache.nowflt')
    def test_check__checksum_same__part_none__cache_new(self, nowflt, fp):
        # Prepare test
        self.key = self.test_check__checksum_same__part_none__cache_new.__name__
        self.part = None
        nowflt.return_value = self.now + 1
        self.cache.fp = fp
        self.cache.cache_dict[self.key] = self.cache_entry
        self.cache.count += 1
        # Execute test
        result = self.cache.check(self.key, self.path, self.part)

        # Evaluate internal state (attributes values)
        self.assertIsNone(self.cache.cache_hit, ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_hit'))
        self.assertTrue(result, ASSERT_INVALID_RETURNED_VALUE_FMT.format('sr_cache.check'))
        expected = {self.key: self.cache_entry}
        self.assertDictEqual(expected, self.cache.cache_dict, ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_dict'))
        self.assertEqual(self.count + 2, self.cache.count, ASSERT_INVALID_VALUE_FMT.format('sr_cache.count'))

        # Evaluate external calls
        expected = [call.write(WRITE_LINE_FMT.format(self.key, nowflt.return_value, self.file, self.part))]
        self.assertEqual(expected, fp.mock_calls, ASSERT_MOCK_CALLS)

    @patch('_io.TextIOWrapper')
    @patch('sarra.sr_cache.nowflt')
    def test_check__checksum_same__part_weird__cache_new(self, nowflt, fp):
        # Prepare test
        self.key = self.test_check__checksum_same__part_weird__cache_new.__name__
        weird_part = 'p,457,1'
        nowflt.return_value = self.now + 1
        self.cache.fp = fp
        self.cache.cache_dict[self.key] = self.cache_entry
        self.cache.count += 1
        # Execute test
        result = self.cache.check(self.key, self.path, weird_part)

        # Evaluate internal state (attributes values)
        self.assertTrue(result, ASSERT_INVALID_RETURNED_VALUE_FMT.format('sr_cache.check'))
        self.assertIsNone(self.cache.cache_hit, ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_hit'))
        expected = {self.key: self.cache_entry}
        self.assertDictEqual(expected, self.cache.cache_dict, ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_dict'))
        self.assertEqual(self.count + 2, self.cache.count, ASSERT_INVALID_VALUE_FMT.format('sr_cache.count'))

        # Evaluate external calls
        expected = [call.write(WRITE_LINE_FMT.format(self.key, nowflt.return_value, self.file, weird_part))]
        self.assertEqual(expected, fp.mock_calls, ASSERT_MOCK_CALLS)

    @patch('_io.TextIOWrapper')
    @patch('sarra.sr_cache.nowflt')
    def test_check__checksum_same__part_differ__cache_hit(self, nowflt, fp):
        # Prepare test
        self.key = self.test_check__checksum_same__part_differ__cache_hit.__name__
        different_part = 'p,457,3,46,1'
        nowflt.return_value = self.now + 1
        self.cache.fp = fp
        self.cache.cache_dict[self.key] = self.cache_entry
        self.cache.count += 1
        # Execute test
        result = self.cache.check(self.key, self.path, different_part)

        # Evaluate internal state (attributes values)
        self.assertFalse(result, ASSERT_INVALID_RETURNED_VALUE_FMT.format('sr_cache.check'))
        assert_msg = ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_hit')
        self.assertEqual(f'{self.file}*{different_part[:-5]}', self.cache.cache_hit[:-5], assert_msg)
        expected = {self.key: self.cache_entry}
        assert_msg = ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_dict')
        self.assertDictEqual(expected, self.cache.cache_dict, assert_msg)
        assert_msg = ASSERT_INVALID_VALUE_FMT.format('sr_cache.count')
        self.assertEqual(self.count + 2, self.cache.count, assert_msg)

        # Evaluate external calls
        expected = [call.write(WRITE_LINE_FMT.format(self.key, nowflt.return_value, self.file, different_part))]
        self.assertEqual(expected, fp.mock_calls, ASSERT_MOCK_CALLS)

    @patch('_io.TextIOWrapper')
    @patch('sarra.sr_cache.nowflt')
    def test_check__checksum_same__part_differ__cache_new(self, nowflt, fp):
        # Prepare test
        self.key = self.test_check__checksum_same__part_differ__cache_new.__name__
        different_part = 'p,457,3,46,2'
        nowflt.return_value = self.now + 1
        self.cache.fp = fp
        self.cache.cache_dict[self.key] = self.cache_entry
        self.cache.count += 1
        # Execute test
        result = self.cache.check(self.key, self.path, different_part)

        # Evaluate internal state (attributes values)
        self.assertTrue(result, ASSERT_INVALID_RETURNED_VALUE_FMT.format('sr_cache.check'))
        expected = {self.key: self.cache_entry}
        self.assertDictEqual(expected, self.cache.cache_dict, ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_dict'))
        self.assertEqual(self.count + 2, self.cache.count, ASSERT_INVALID_VALUE_FMT.format('sr_cache.count'))

        # Evaluate external calls
        expected = [call.write(WRITE_LINE_FMT.format(self.key, nowflt.return_value, self.file, different_part))]
        self.assertEqual(expected, fp.mock_calls, ASSERT_MOCK_CALLS)

    def test_check_msg(self):
        # Prepare test
        self.key = self.test_check_msg.__name__
        self.cache.check = Mock(return_value=True)
        msg = Mock()
        msg.relpath = self.path
        msg.headers = {'sum': self.key, 'parts': self.part}
        # Execute test
        self.cache.check_msg(msg)

        # Evaluate results
        expected = [call(self.key, self.file, self.part)]
        self.assertEqual(expected, self.cache.check.mock_calls, ASSERT_MOCK_CALLS)

    def test_check_msg__cache_basis_path(self):
        # Prepare test
        self.key = self.test_check_msg__cache_basis_path.__name__
        self.cache.cache_basis = CacheBasis.path.name
        self.cache.check = Mock(return_value=True)
        msg = Mock()
        msg.relpath = self.path
        msg.headers = {'sum': self.key, 'parts': self.part}
        # Execute test
        self.cache.check_msg(msg)

        # Evaluate results
        expected = [call(self.key, self.path, self.part)]
        self.assertEqual(expected, self.cache.check.mock_calls, ASSERT_MOCK_CALLS)

    def test_check_msg__cache_basis_data(self):
        # Prepare test
        self.key = self.test_check_msg__cache_basis_data.__name__
        self.cache.cache_basis = CacheBasis.data.name
        self.cache.check = Mock(return_value=True)
        msg = Mock()
        msg.relpath = self.path
        msg.headers = {'sum': self.key, 'parts': self.part}
        # Execute test
        self.cache.check_msg(msg)

        # Evaluate results
        expected = [call(self.key, CacheBasis.data.name, self.part)]
        self.assertEqual(expected, self.cache.check.mock_calls, ASSERT_MOCK_CALLS)

    def test_check_msg__sum_L(self):
        # Prepare test
        self.key = f"L,{self.test_check_msg__sum_L.__name__}"
        self.cache.check = Mock(return_value=True)
        msg = Mock()
        msg.relpath = self.path
        msg.headers = {'sum': self.key, 'parts': self.part}
        # Execute test
        self.cache.check_msg(msg)

        # Evaluate results
        expected = [call(self.key, self.file, self.file)]
        self.assertEqual(expected, self.cache.check.mock_calls, ASSERT_MOCK_CALLS)

    @patch('sarra.sr_cache.nowflt')
    def test_clean(self, nowflt):
        # Prepare test
        self.key = self.test_clean.__name__
        nowflt.return_value = self.now
        self.cache.expire = 50
        self.then = self.now - 100
        self.then_key = KEY_FMT.format(self.key, 'expired')
        self.cache.cache_dict[self.key] = self.cache_entry
        self.cache.cache_dict[self.then_key] = {ENTRY_KEY_FMT.format(self.file, self.part): self.then}
        # Execute test
        self.cache.clean()

        # Evaluate results
        self.assertIn(self.key, self.cache.cache_dict, ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_dict'))
        self.assertEqual(1, len(self.cache.cache_dict), ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_dict size'))
        self.assertEqual(1, self.cache.count, ASSERT_INVALID_VALUE_FMT.format('sr_cache.count'))

    @patch('_io.TextIOWrapper')
    @patch('sarra.sr_cache.nowflt')
    def test_clean__fp(self, nowflt, fp):
        # Prepare test
        self.key = self.test_clean__fp.__name__
        nowflt.return_value = self.now
        self.cache.expire = 50
        self.then = self.now - 100
        self.then_key = KEY_FMT.format(self.key, 'expired')
        self.cache.cache_dict[self.key] = self.cache_entry
        self.cache.cache_dict[self.then_key] = {ENTRY_KEY_FMT.format(self.file, self.part): self.then}
        # Execute test
        self.cache.clean(fp)

        # Evaluate results
        expected = [call.__bool__(), call.write('{} {:f} {} {}\n'.format(self.key, self.now, self.file, self.part))]
        self.assertEqual(expected, fp.mock_calls, ASSERT_MOCK_CALLS)

    @patch('sarra.sr_cache.nowflt')
    def test_clean__delpath(self, nowflt):
        # Prepare test
        self.key = self.test_clean__delpath.__name__
        nowflt.return_value = self.now
        self.cache.expire = 50
        self.then = self.now - 100
        self.then_key = KEY_FMT.format(self.key, 'expired')
        self.cache.cache_dict[self.key] = self.cache_entry
        self.cache.cache_dict[self.then_key] = {ENTRY_KEY_FMT.format(self.file, self.part): self.then}
        # Execute test
        self.cache.clean(delpath=self.file)

        # Evaluate results
        self.assertEqual({}, self.cache.cache_dict, ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_dict'))

    @patch('sarra.sr_cache.nowflt')
    def test_clean__delpath__unmatched_cache_basis(self, nowflt):
        # Prepare test
        self.key = self.test_clean__delpath__unmatched_cache_basis.__name__
        nowflt.return_value = self.now
        self.cache.expire = 50
        self.then = self.now - 100
        self.then_key = KEY_FMT.format(self.key, 'expired')
        self.cache.cache_dict[self.key] = self.cache_entry
        self.cache.cache_dict[self.then_key] = {ENTRY_KEY_FMT.format(self.file, self.part): self.then}
        # Execute test
        self.cache.clean(delpath=self.path)

        # Evaluate results
        self.assertEqual(1, len(self.cache.cache_dict), ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_dict size'))

    def test_clean__cache_dict_empty(self):
        # Prepare test
        # Execute test
        self.cache.clean()

        # Evaluate results
        self.assertEqual({}, self.cache.cache_dict, ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_dict'))

    @patch('sarra.sr_cache.nowflt')
    def test_clean__cache_dict__no_expired(self, nowflt):
        # Prepare test
        self.key = self.test_clean__cache_dict__no_expired.__name__
        nowflt.return_value = self.now
        self.cache.expire = 50
        self.then = self.now - 10
        self.then_key = KEY_FMT.format(self.key, 'not_expired')
        self.cache.cache_dict[self.key] = self.cache_entry
        self.cache.cache_dict[self.then_key] = {ENTRY_KEY_FMT.format(self.file, self.part): self.then}
        # Execute test
        self.cache.clean()

        # Evaluate results
        self.assertIn(self.key, self.cache.cache_dict, ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_dict'))
        self.assertIn(self.then_key, self.cache.cache_dict, ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_dict'))
        self.assertEqual(2, len(self.cache.cache_dict), ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_dict size'))
        self.assertEqual(2, self.cache.count, ASSERT_INVALID_VALUE_FMT.format('sr_cache.count'))

    @patch('_io.TextIOWrapper')
    def test_close(self, fp):
        # Prepare test
        self.key = self.test_close.__name__
        self.cache.fp = fp
        self.cache.cache_dict[self.key] = self.cache_entry
        self.cache.count = 1
        # Execute test
        self.cache.close()

        # Evaluate internal state (attribute values)
        self.assertIsNone(self.cache.fp, ASSERT_INVALID_VALUE_FMT.format('sr_cache.fp'))
        self.assertDictEqual({}, self.cache.cache_dict, ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_dict'))
        self.assertEqual(0, self.cache.count, ASSERT_INVALID_VALUE_FMT.format('sr_cache.count'))

        # Evaluate external calls
        expected = [call.flush(), call.close()]
        self.assertEqual(expected, fp.mock_calls)

    @patch('sarra.sr_cache.os')
    @patch('_io.TextIOWrapper')
    def test_close__unlink(self, fp, mocked_os):
        # Prepare test
        self.key = self.test_close__unlink.__name__
        self.cache.fp = fp
        self.cache.cache_dict[self.key] = self.cache_entry
        self.cache.count = 1
        # Execute test
        self.cache.close(unlink=True)

        # Evaluate results
        expected = [call.unlink(self.cache.cache_file)]
        self.assertEqual(expected, mocked_os.mock_calls, ASSERT_MOCK_CALLS)

    @patch('sarra.sr_cache.os')
    @patch('builtins.open')
    @patch('_io.TextIOWrapper')
    def test_delete_path(self, fp, mocked_open, mocked_os):
        # Prepare test
        self.key = self.test_delete_path.__name__
        self.cache.clean = Mock()
        self.cache.fp = fp
        self.cache.cache_dict[self.key] = self.cache_entry
        self.cache.count = 1
        # Execute test
        self.cache.delete_path(self.path)

        # Evaluate internal state (attribute values)
        self.assertNotEqual(fp, self.cache.fp, ASSERT_INVALID_VALUE_FMT.format('sr_cache.fp'))
        self.assertEqual(mocked_open(), self.cache.fp, ASSERT_INVALID_VALUE_FMT.format('sr_cache.fp'))

        # Evaluate external calls
        expected = [call.unlink(self.cache.cache_file)]
        self.assertIn(expected, mocked_os.mock_calls, ASSERT_MOCK_CALLS)
        self.cache.clean.assert_called_once_with(self.cache.fp, self.path)

    @patch('sarra.sr_cache.os')
    @patch('builtins.open')
    @patch('_io.TextIOWrapper')
    def test_free(self, fp, mocked_open, mocked_os):
        # Prepare test
        self.key = self.test_free.__name__
        self.cache.fp = fp
        self.cache.cache_dict[self.key] = self.cache_entry
        self.cache.count = 1
        # Execute test
        self.cache.free()

        # Evaluate internal state (attribute values)
        self.assertNotEqual(fp, self.cache.fp, ASSERT_INVALID_VALUE_FMT.format('sr_cache.fp'))
        self.assertEqual(mocked_open(), self.cache.fp, ASSERT_INVALID_VALUE_FMT.format('sr_cache.fp'))
        self.assertEqual({}, self.cache.cache_dict, ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_dict'))
        self.assertEqual(0, self.cache.count, ASSERT_INVALID_VALUE_FMT.format('sr_cache.count'))

        # Evaluate external calls
        expected = [call.unlink(self.cache.cache_file)]
        self.assertEqual(expected, mocked_os.mock_calls, ASSERT_MOCK_CALLS)

    @patch('sarra.sr_cache.nowflt')
    @patch('sarra.sr_cache.os')
    @patch('builtins.open')
    @patch('_io.TextIOWrapper')
    def test_load(self, fp, mocked_open, mocked_os, nowflt):
        # Prepare test
        self.key = self.test_load.__name__
        self.then_key = KEY_FMT.format(self.key, 'not_expired')
        self.then = self.now - 10
        self.previous_entry = {self.entry_key: self.then}
        nowflt.return_value = self.now
        mocked_open.return_value = fp
        fp.readline.return_value = ''
        fp.readline.side_effect = [
            WRITE_LINE_FMT.format(self.then_key, self.then, self.file, self.part),
            WRITE_LINE_FMT.format(self.key, self.now, self.file, self.part),
            DEFAULT
        ]
        self.cache.expire = 100
        # Execute test
        self.cache.load()

        # Evaluate results
        expected = {
            self.key: {self.entry_key: float('{:f}'.format(self.now))},
            self.then_key: {self.entry_key: float('{:f}'.format(self.then))}
        }
        # TODO add expire entry
        self.assertEqual(expected, self.cache.cache_dict, ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_dict'))

    def test_open(self):
        # Prepare test
        self.user_cache_dir = os.path.join('user', 'cache', 'dir')
        self.instance = 1
        self.cache.load = Mock()
        # Execute test
        self.cache.open()

        # Evaluate results
        self.dest_path = os.path.join(self.user_cache_dir, f'recent_files_{self.instance:03}.cache')
        self.assertEqual(self.dest_path, self.cache.cache_file, ASSERT_INVALID_VALUE_FMT.format('sr_cache.cache_file'))
        self.cache.load.assert_called()

    @patch('sarra.sr_cache.os')
    @patch('builtins.open')
    @patch('_io.TextIOWrapper')
    def test_save(self, fp, mocked_open, mocked_os):
        # Prepare test
        self.cache.clean = Mock()
        self.cache.fp = fp
        # Execute test
        self.cache.save()

        # Evaluate results
        expected = [call.__bool__(), call.close()]
        self.assertEqual(expected, fp.mock_calls, ASSERT_MOCK_CALLS)
        expected = [call(self.cache.cache_file, 'w')]
        self.assertEqual(expected, mocked_open.mock_calls, ASSERT_MOCK_CALLS)
        expected = [call.unlink(self.cache.cache_file)]
        self.assertEqual(expected, mocked_os.mock_calls, ASSERT_MOCK_CALLS)
        self.cache.clean.assert_called_with(mocked_open())

    @patch('sarra.sr_cache.nowflt')
    def test_check_expire(self, nowflt):
        # Prepare test
        nowflt.return_value = self.now
        self.cache.last_expire = self.now - 1000
        self.cache.expire = 100
        self.cache.clean = Mock()
        # Execute test
        self.cache.check_expire()

        # Evaluate results
        self.cache.clean.assert_called()
        self.assertEqual(self.now, self.cache.last_expire, ASSERT_INVALID_VALUE_FMT.format('sr_cache.last_expire'))


class CacheBasis(Enum):
    name = auto()
    path = auto()
    data = auto()


def suite():
    """ Create the test suite that include all sr_amqp test cases

    :return: sr_amqp test suite
    """
    sr_amqp_suite = unittest.TestSuite()
    sr_amqp_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(SrCacheCase))
    return sr_amqp_suite


if __name__ == 'main':
    runner = unittest.TextTestRunner()
    runner.run(suite())
