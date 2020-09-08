""" This file is part of metpx-sarracenia.

metpx-sarracenia
Documentation: https://github.com/MetPX/sarracenia

sr_sarra_unit_test.py : test utility tool used for sr_sarra


Code contributed by:
 Benoit Lapointe - Shared Services Canada
"""
import unittest

try:
    from sr_sarra import *
except ImportError:
    from sarra.sr_sarra import *


class SrSarraTestCase(unittest.TestCase):
    """ The parent class of all sr_sarra test cases """
    sarra = None
    orig_exit = None

    @classmethod
    def setUpClass(cls) -> None:
        """ Setup basic config file with basic include

        :return: None
        """
        f = open("./aaa.conf", "w")
        f.write("broker amqp://tfeed@${FLOWBROKER}/\n")
        f.write("exchange xsarra\n")
        f.write("notify_only\n")
        f.close()
        cls.sarra = sr_sarra("aaa")
        cls.orig_exit = os._exit
        os._exit = sys.exit

    @classmethod
    def tearDownClass(cls) -> None:
        """ Remove configs for sr_sarra tests

        :return: None
        """
        os.unlink("./aaa.conf")
        os.removedirs(cls.sarra.user_cache_dir)
        os._exit = cls.orig_exit

    def test_notify_only_exit(self):
        self.assertTrue(self.sarra.notify_only,
                        "notify_only option does not work properly")


def suite():
    """ Create the test suite that include all sr_sarra test cases

    :return: sr_sarra test suite
    """
    sr_sarra_suite = unittest.TestSuite()
    sr_sarra_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(SrSarraTestCase))
    return sr_sarra_suite


if __name__ == 'main':
    runner = unittest.TextTestRunner()
    runner.run(suite())
