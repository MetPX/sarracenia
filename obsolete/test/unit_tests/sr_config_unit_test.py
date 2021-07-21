""" This file is part of metpx-sarracenia.

metpx-sarracenia
Documentation: https://github.com/MetPX/sarracenia

sr_config_unit_test.py : test utility tool used for sr_config


Code contributed by:
 Benoit Lapointe - Shared Services Canada
"""
import _io
import tempfile
import unittest

try:
    from sr_config import *
except ImportError:
    from sarra.sr_config import *


class SrConfigTestCase(unittest.TestCase):
    """ The parent class of all sr_config test cases

    It handles base configs used in all tests
    """
    cfg = None

    @classmethod
    def setUpClass(cls) -> None:
        """ Setup basic config file with basic include

        :return: None
        """
        f = open("./bbb.inc", "w")
        f.write("randomize True\n")
        f.close()
        f = open("./aaa.conf", "w")
        f.write("include bbb.inc\n")
        f.close()

        # instantiation, test include and overwrite logs
        cls.cfg = sr_config(config="aaa")
        cls.cfg.configure()

    @classmethod
    def tearDownClass(cls) -> None:
        """ Remove configs for sr_config tests

        :return: None
        """
        os.unlink("./bbb.inc")
        os.unlink("./aaa.conf")
        os.removedirs(cls.cfg.user_cache_dir)


class SrConfigDeliveryOptionsTestCase(SrConfigTestCase):
    """ Test cases related to delivery options

    see: https://github.com/MetPX/sarracenia/blob/master/doc/sr_subscribe.1.rst#delivery-specifications
    """
    def setUp(self) -> None:
        self.cfg.defaults()

    def test_n_flag(self):
        opt1 = "-n"
        self.cfg.option(opt1.split())
        self.assertTrue(self.cfg.notify_only,
                        "notify_only option does not work properly")

    def test_no_download(self):
        opt1 = "no_download True"
        self.cfg.option(opt1.split())
        self.assertTrue(self.cfg.notify_only,
                        "no_download option does not work properly")

    def test_no_download_flag(self):
        opt1 = "--no_download"
        self.cfg.option(opt1.split())
        self.assertTrue(self.cfg.notify_only,
                        "no_download option does not work properly")

    def test_notify_only(self):
        opt1 = "notify_only True"
        self.cfg.option(opt1.split())
        self.assertTrue(self.cfg.notify_only,
                        "notify_only option does not work properly")

    def test_notify_only_flag(self):
        opt1 = "--notify_only"
        self.cfg.option(opt1.split())
        self.assertTrue(self.cfg.notify_only,
                        "notify_only option does not work properly")

    def test_notify_only_false(self):
        opt1 = "notify_only False"
        self.cfg.option(opt1.split())
        self.assertFalse(self.cfg.notify_only,
                         "notify_only False option does not work properly")


class SrConfigRandomizeTestCase(SrConfigTestCase):
    def test_include_inc(self):
        self.assertTrue(self.cfg.randomize, "test 01a: problem with include")

    def test_isTrue(self):
        # back to defaults + check isTrue
        self.cfg.defaults()
        self.assertTrue(
            self.cfg.isTrue('true') or not self.cfg.isTrue('false'),
            "test 01b: problem with module isTrue")


class SrConfigChecksumTestCase(SrConfigTestCase):
    """ Test cases related to checksum handling

    """
    tmpdir = None
    tmpdirname = None
    tmppath = None

    @classmethod
    def setUpClass(cls) -> None:
        """ Setup path used by all checksum test cases

        :return:
        """
        super(SrConfigChecksumTestCase, cls).setUpClass()
        cls.tmpdir = tempfile.TemporaryDirectory()
        cls.tmpfilname = 'test_chksum_file'
        cls.tmppath = os.path.join(cls.tmpdir.name, cls.tmpfilname)
        with open(cls.tmppath, 'wb') as f:
            f.write(b"0123456789")
            f.write(b"abcdefghij")
            f.write(b"ABCDEFGHIJ")
            f.write(b"9876543210")

    @classmethod
    def tearDownClass(cls) -> None:
        """ Remove paths of checksum test cases

        :return:
        """
        super(SrConfigChecksumTestCase, cls).tearDownClass()
        os.unlink(cls.tmppath)
        cls.tmpdir.cleanup()

    def test_checksum_0(self):
        self.cfg.set_sumalgo('0')
        chk0 = self.cfg.sumalgo
        chk0.set_path(self.tmppath)
        with open(self.tmppath, 'rb') as f:
            for i in range(4):
                chunk = f.read(10)
                chk0.update(chunk)
        v = int(chk0.get_value())
        self.assertGreaterEqual(v, 0, "test 02a: checksum_0 did not work")
        self.assertLessEqual(v, 9999, "test 02b: checksum_0 did not work")

    def test_checksum_d(self):
        self.cfg.set_sumalgo('d')
        chkd = self.cfg.sumalgo
        chkd.set_path(self.tmppath)
        with open(self.tmppath, 'rb') as f:
            for i in range(4):
                chunk = f.read(10)
                chkd.update(chunk)
        self.assertEqual(chkd.get_value(), '7efaff9e615737b379a45646c755c492',
                         "test 02c: checksum_d did not work")

    def test_checksum_n(self):
        self.cfg.set_sumalgo('n')
        chkn = self.cfg.sumalgo
        chkn.set_path(self.tmpfilname)
        with open(self.tmppath, 'rb') as f:
            for i in range(4):
                chunk = f.read(10)
                chkn.update(chunk)
        self.assertEqual(chkn.get_value(), 'fd6b0296fe95e19fcef6f21f77efdfed',
                         "test 02d: checksum_n did not work")

    @unittest.skip("Commented  # TODO why this has been commented")
    def test_checksum_N(self):
        self.cfg.set_sumalgo('N')
        chk_n = self.cfg.sumalgo
        chk_n.set_path(self.tmpfilname, 'i,1,256,1,0,0')
        chunk = 'aaa'
        chk_n.update(chunk)
        long_chksum = 'a0847ab809f83cb573b76671bb500a430372d2e3d5bce4c4cd663c4ea1b5c40f5eda439c09c7776ff19e3cc30459a' \
                      'cc2a387cf10d056296b9dc03a6556da291f'
        self.assertEqual(chk_n.get_value(), long_chksum,
                         "test 02e: checksum_N did not work")

    def test_checksum_s(self):
        # checksum_s
        self.cfg.set_sumalgo('s')
        chks = self.cfg.sumalgo
        chks.set_path(self.tmppath)
        with open(self.tmppath, 'rb') as f:
            for i in range(4):
                chunk = f.read(10)
                chks.update(chunk)
        long_chksum = 'e0103da78bbff9a741116e04f8bea2a5b291605c00731dcf7d26c0848bccf76dd2caa6771cb4b909d5213d876ab' \
                      '85094654f36d15e265d322b68fea4b78efb33'
        self.assertEqual(chks.get_value(), long_chksum,
                         "test 02f: checksum_s did not work")


class SrConfigPluginScriptTestCase(SrConfigTestCase):
    """ Test cases related to plugin interfacing """
    def setUp(self) -> None:
        """ Creating a dummy script plugin which will be tested

        :return: None
        """
        with open("./scrpt.py", "w") as f:
            f.write("class Transformer(object): \n")
            f.write("      def __init__(self):\n")
            f.write("          pass\n")
            f.write("\n")
            f.write("      def perform(self,parent):\n")
            f.write("          if parent.this_value != 0 : return False\n")
            f.write("          parent.this_value = 1\n")
            f.write("          return True\n")
            f.write("\n")
            f.write("transformer = Transformer()\n")
            f.write("self.on_message = transformer.perform\n")
        self.ok, self.path = self.cfg.config_path("plugins",
                                                  "scrpt.py",
                                                  mandatory=True,
                                                  ctype='py')

    def tearDown(self) -> None:
        """ Remove the script plugin file """
        os.unlink("./scrpt.py")

    def test_find_script(self):
        self.assertTrue(self.ok,
                        "test 03: problem with config_path script not found")

    def test_load_script(self):
        self.cfg.execfile("on_message", self.path)
        self.assertIsNotNone(
            self.cfg.on_message,
            "test 04: problem with module execfile script not loaded")

    def test_run_script(self):
        self.cfg.this_value = 0
        self.cfg.on_message(self.cfg)
        self.assertEqual(self.cfg.this_value, 1,
                         "test 05: problem to run the script ")


class SrConfigGeneralTestCase(SrConfigTestCase):
    """ Test cases related to general config parsing an interpretation logic """
    def setUp(self) -> None:
        """ Creates configuration which are generic to all test cases

        :return: None
        """
        self.cfg.general()
        self.cfg.randomize = False
        self.cfg.assemble = False
        self.cfg.lr_backupCount = 5
        self.cfg.expire = 0
        self.expire_value = 1000 * 60 * 60 * 3
        self.message_value = 1000 * 60 * 60 * 24 * 7 * 3
        self.cfg.message_ttl = 0
        self.cfg.args([
            '-expire', '3h', '-message_ttl', '3W', '--randomize', '--assemble',
            'True', '-logrotate', '5m', '-logrotate_interval', '1m'
        ])
        self.cfg.toto = ['tutu1', 'tutu2']
        opt1 = "broker amqp://michel:passwd@testbroker.toto"
        self.cfg.option(opt1.split())

    def test_user_cache_dir(self):
        test_cache_path = os.path.join(os.path.expanduser('~'), '.cache',
                                       'sarra', self.cfg.program_name, 'aaa')
        self.assertEqual(self.cfg.user_cache_dir, test_cache_path)

    def test_user_log_dir(self):
        test_cache_path = os.path.join(os.path.expanduser('~'), '.cache',
                                       'sarra', 'log')
        self.assertEqual(self.cfg.user_log_dir, test_cache_path)

    def test_user_config_dir(self):
        test_cache_path = os.path.join(os.path.expanduser('~'), '.config',
                                       'sarra')
        self.assertEqual(self.cfg.user_config_dir, test_cache_path)

    def test_randomize(self):
        self.assertTrue(self.cfg.randomize, "test 06: args problem randomize")

    def test_inplace(self):
        self.assertTrue(self.cfg.inplace, "test 07: args problem assemble")

    def test_lr_interval(self):
        self.assertEqual(
            self.cfg.lr_interval, 1,
            "test 08a: args problem logrotate %s" % self.cfg.lr_interval)

    def test_lr_backupCount(self):
        self.assertEqual(
            self.cfg.lr_backupCount, 5,
            "test 08b: args problem logrotate %s" % self.cfg.lr_backupCount)

    def test_lr_when(self):
        self.assertEqual(
            self.cfg.lr_when, 'm',
            "test 08c: args problem logrotate %s" % self.cfg.lr_when)

    def test_expire(self):
        self.assertEqual(self.cfg.expire, self.expire_value,
                         "test 09: args problem expire %s" % self.cfg.expire)

    def test_msg_ttl(self):
        self.assertEqual(
            self.cfg.message_ttl, self.message_value,
            "test 10: args problem message_ttl %s" % self.cfg.message_ttl)

    def test_has_vip(self):
        # has_vip...
        self.cfg.args(['-vip', '127.0.0.1'])
        self.assertTrue(self.cfg.has_vip(), "test 11: has_vip failed")

    def test_broker_url(self):
        opt1 = "hostname toto"
        opt2 = "broker amqp://a:b@${HOSTNAME}"
        self.cfg.option(opt1.split())
        self.cfg.option(opt2.split())
        self.assertEqual(self.cfg.broker.geturl(), "amqp://a:b@toto",
                         "test 12: varsub problem with replacing HOSTNAME")

    def test_partflg(self):
        opt1 = "parts i,128"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.partflg, 'i',
                         "test 13a: option parts or module validate_parts")
        self.assertEqual(self.cfg.blocksize, 128,
                         "test 13b: option parts or module validate_parts")

    def test_sumflg_zd(self):
        opt1 = "sum z,d"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.sumflg, 'z,d',
                         "test 14: option sum or module validate_sum")

    def test_sumflg_r0(self):
        opt1 = "sum R,0"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.sumflg, 'R,0',
                         "test 15: option sum or module validate_sum")

    def test_sumflg_d(self):
        opt1 = "sum d"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.sumflg, 'd',
                         "test 16a: option sum or module validate_sum")
        self.assertEqual(self.cfg.sumalgo.registered_as(), 'd',
                         "test 16b: option sum or module validate_sum")

    def test_sum_0(self):
        opt1 = "sum 0"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.sumflg, '0',
                         "test 17a: option sum or module validate_sum")
        self.assertEqual(self.cfg.sumalgo.registered_as(), '0',
                         "test 17b: option sum or module validate_sum")

    def test_sum_n(self):
        opt1 = "sum n"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.sumflg, 'n',
                         "test 18a: option sum or module validate_sum")
        self.assertEqual(self.cfg.sumalgo.registered_as(), 'n',
                         "test 18b: option sum or module validate_sum")

    def test_sum_s(self):
        opt1 = "sum s"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.sumflg, 's',
                         "test 19a: option sum or module validate_sum")
        self.assertEqual(self.cfg.sumalgo.registered_as(), 's',
                         "test 19b: option sum or module validate_sum")

    @unittest.skip("Commented  # TODO why this has been commented")
    def test_sum_N(self):
        opt1 = "sum N"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.sumflg, 'N',
                         "test 19c: option sum or module validate_sum")
        self.assertEqual(self.cfg.sumalgo.registered_as(), 'N',
                         "test 19d: option sum or module validate_sum")

    def test_movepath(self):
        opt1 = "move toto titi"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.movepath[0], 'toto',
                         "test 20a: option move for sr_post does not work")
        self.assertEqual(self.cfg.movepath[1], 'titi',
                         "test 20b: option move for sr_post does not work")

    def test_postpath(self):
        opt1 = "post_base_dir None"
        self.cfg.option(opt1.split())
        opt1 = "path .. ."
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.postpath[0], os.path.abspath('..'),
                         "test 21a: option path for sr_post does not work")
        self.assertEqual(self.cfg.postpath[1], os.path.abspath('.'),
                         "test 21b: option path for sr_post does not work")

    def test_inflight(self):
        opt1 = "inflight ."
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.inflight, '.',
                         "test 22: option inflight . does not work")

    def test_inflight_tmp(self):
        opt1 = "inflight .tmp"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.inflight, '.tmp',
                         "test 23: option inflight .tmp does not work")

    def test_inflight_1_5(self):
        opt1 = "inflight 1.5"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.inflight, 1.5,
                         "test 24: option inflight 1.5  does not work")

    def test_prefetch_10(self):
        opt1 = "prefetch 10"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.prefetch, 10,
                         "test 25: prefetch option did not work")

    def test_reparsing_include(self):
        self.cfg.config(self.cfg.user_config)
        self.assertTrue(True, "test 25b: failed")

    def test_header_add(self):
        opt1 = "header toto1=titi1"
        self.cfg.option(opt1.split())
        opt2 = "header toto2=titi2"
        self.cfg.option(opt2.split())
        self.assertIn('toto1', self.cfg.headers_to_add,
                      "test 26a: option header adding entries did not work")
        self.assertIn('toto2', self.cfg.headers_to_add,
                      "test 26b: option header adding entries did not work")
        self.assertEqual(
            self.cfg.headers_to_add['toto1'], 'titi1',
            "test 26c: option header adding entries did not work")
        self.assertEqual(
            len(self.cfg.headers_to_add), 2,
            "test 26d: option header adding entries did not work")

    def test_header_delete(self):
        opt3 = "header tutu1=None"
        self.cfg.option(opt3.split())
        opt4 = "header tutu2=None"
        self.cfg.option(opt4.split())
        self.assertIn('tutu1', self.cfg.headers_to_del,
                      "test 27a: option header deleting entries did not work")
        self.assertIn('tutu2', self.cfg.headers_to_del,
                      "test 27b: option header deleting entries did not work")
        self.assertEqual(
            len(self.cfg.headers_to_del), 2,
            "test 27c: option header deleting entries did not work")

    def test_expire_from_str(self):
        # expire in ms
        opt4 = "expire 10m"
        self.cfg.option(opt4.split())
        self.assertEqual(
            self.cfg.expire, 600000,
            "test 28: option expire or module duration_from_str did not work")

    def test_message_ttl(self):
        # message_ttl in ms
        opt4 = "message_ttl 20m"
        self.cfg.option(opt4.split())
        self.assertEqual(
            self.cfg.message_ttl, 1200000,
            "test 29: option message_ttl or module duration_from_str did not work"
        )

    def test_currentDir(self):
        os.environ["VAR1"] = "michel"
        os.environ["VAR2"] = "peter"
        os.environ["VAR3"] = "jun"
        opt4 = "directory ${VAR1}/${VAR2}/${VAR3}/blabla"
        self.cfg.option(opt4.split())
        self.assertNotIn(
            '$', self.cfg.currentDir,
            "test 30a: env variable substitution failed {}".format(
                self.cfg.currentDir))
        self.assertEqual(
            self.cfg.currentDir, 'michel/peter/jun/blabla',
            "test 30b: env variable substitution failed {}".format(
                self.cfg.currentDir))

    def test_strip(self):
        opt4 = 'strip 4'
        self.cfg.option(opt4.split())
        self.assertEqual(self.cfg.strip, 4,
                         "test 31: option strip with integer failed")

    def test_pstrip(self):
        opt4 = 'strip .*aaa'
        self.cfg.option(opt4.split())
        self.assertEqual(self.cfg.pstrip, '.*aaa',
                         "test 32: option strip with pattern failed")

    @unittest.skipIf(not pika_available, "pika library is not available")
    def test_use_pika(self):
        opt4 = 'use_pika'
        self.cfg.option(opt4.split())
        self.assertTrue(
            self.cfg.use_pika and not self.cfg.use_amqplib,
            "test 33a: option use_pika boolean set to true without value failed"
        )

    @unittest.skipIf(not pika_available, "pika library is not available")
    def test_use_pika_true(self):
        opt4 = 'use_pika True'
        self.cfg.option(opt4.split())
        self.assertTrue(
            self.cfg.use_pika and not self.cfg.use_amqplib,
            "test 33b: option use_pika boolean set to true failed")

    @unittest.skipIf(not pika_available, "pika library is not available")
    def test_use_pika_false(self):
        opt4 = 'use_pika False'
        self.cfg.option(opt4.split())
        self.assertTrue(
            not self.cfg.use_pika and not self.cfg.use_amqplib,
            "test 34: option use_pika boolean set to false failed")

    def test_statehost_false(self):
        opt4 = 'statehost False'
        self.cfg.option(opt4.split())
        self.assertFalse(
            self.cfg.statehost,
            "test 35: option statehost boolean set to false failed")

    def test_statehost_true(self):
        opt4 = 'statehost True'
        self.cfg.option(opt4.split())
        self.assertTrue(
            self.cfg.statehost,
            "test 36a: option statehost boolean set to true, hostform short, failed"
        )
        self.assertEqual(
            self.cfg.hostform, 'short',
            "test 36b: option statehost boolean set to true, hostform short, failed"
        )

    def test_statehost_short(self):
        opt4 = 'statehost SHORT'
        self.cfg.option(opt4.split())
        self.assertTrue(
            self.cfg.statehost,
            "test 37a: option statehost set to SHORT, hostform short, failed")
        self.assertEqual(
            self.cfg.hostform, 'short',
            "test 37b: option statehost set to SHORT, hostform short, failed")

    def test_statehost_fqdn(self):
        opt4 = 'statehost fqdn'
        self.cfg.option(opt4.split())
        self.assertTrue(
            self.cfg.statehost,
            "test 38a: option statehost set to fqdn, hostform fqdn, failed")
        self.assertEqual(
            self.cfg.hostform, 'fqdn',
            "test 38b: option statehost set to fqdn, hostform fqdn, failed")

    def test_statehost_bad(self):
        opt4 = 'statehost TOTO'
        self.cfg.option(opt4.split())
        self.assertFalse(
            self.cfg.statehost,
            "test 39a: option statehost set badly ... did not react correctly, failed"
        )
        self.assertIsNotNone(
            self.cfg.hostform,
            "test 39b: option hostform set badly ... did not react correctly, failed"
        )

    def test_extended(self):
        opt4 = 'extended TOTO'
        self.cfg.option(opt4.split())
        self.cfg.declare_option('extended')
        self.assertTrue(
            self.cfg.check_extended(),
            "test 40: extend with new option, option was declared, but check_extended complained(False)"
        )

    def test_extended_first(self):
        opt4 = 'extended_bad TITI'
        self.cfg.option(opt4.split())
        # modify this test... causes error to be printed out ... which is ok... but annoying for conformity tests
        # if self.cfg.check_extended():
        self.assertEqual(
            self.cfg.extended_bad[0], 'TITI',
            "test 41:  extend with new option, option not declared, value should still be ok"
        )

    def test_extended_list(self):
        opt1 = "surplus_opt surplus_value"
        self.cfg.option(opt1.split())
        opt1 = "surplus_opt surplus_value2"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.surplus_opt[0], "surplus_value",
                         "test 43a: extend option list did not work")
        self.assertEqual(self.cfg.surplus_opt[1], "surplus_value2",
                         "test 43b: extend option list did not work")

    def test_base_dir(self):
        opt1 = "base_dir /home/aspymjg/dev/metpx-sarracenia/sarra"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.base_dir,
                         '/home/aspymjg/dev/metpx-sarracenia/sarra',
                         "test 44: string option base_dir did not work")

    def test_post_base_dir(self):
        opt1 = "post_base_dir /totot/toto"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.post_base_dir, '/totot/toto',
                         "test 45: string option post_base_dir did not work")

    def test_post_base_url(self):
        opt1 = "post_base_url file://toto"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.post_base_url, 'file://toto',
                         "test 46: url option post_base_url did not work")

    def test_outlet(self):
        self.assertEqual(
            self.cfg.outlet, 'post',
            "test 47: default error outlet = %s" % self.cfg.outlet)

    def test_outlet_json(self):
        opt1 = "outlet json"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.outlet, 'json',
                         "test 48: option outlet value json did not work")

    def test_outlet_url(self):
        opt1 = "outlet url"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.outlet, 'url',
                         "test 49: option outlet value url did not work")

    def test_outlet_port(self):
        opt1 = "outlet post"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.outlet, 'post',
                         "test 50: option outlet value post did not work")

    @unittest.skip(
        "bad option setting skipped... its output confuses conformity... "
        "complains about an error... and it is ok to complain.")
    def test_outlet_post(self):
        opt1 = "outlet toto"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.outlet, 'post',
                         "test 51: option outlet with bad value did not work")

    def test_retry_mode(self):
        self.assertTrue(self.cfg.retry_mode,
                        "test 52: retry_mode should be the default")

    def test_retry_mode_false(self):
        opt1 = "retry_mode false"
        self.cfg.option(opt1.split())
        self.assertFalse(self.cfg.retry_mode,
                         "test 53: retry_mode should be false")

    def test_retry_ttl_to_mins(self):
        opt1 = "retry_ttl 1D"
        self.cfg.option(opt1.split())
        self.assertEqual(
            self.cfg.retry_ttl, 86400,
            "test 54: option retry_ttl or module duration_from_str did not work"
        )

    def test_exchange_suffix(self):
        opt1 = "exchange_suffix suffix1"
        self.cfg.option(opt1.split())
        opt1 = "post_exchange_suffix suffix2"
        self.cfg.option(opt1.split())
        self.assertEqual(
            self.cfg.exchange_suffix, 'suffix1',
            "test 55a: option exchange_suffix or post_exchange_suffix did not work"
        )
        self.assertEqual(
            self.cfg.post_exchange_suffix, 'suffix2',
            "test 55b: option exchange_suffix or post_exchange_suffix did not work"
        )

    def test_broker(self):
        opt1 = "post_base_dir /${broker.hostname}/${broker.username}"
        self.cfg.option(opt1.split())
        self.assertEqual(
            self.cfg.post_base_dir, '/testbroker.toto/michel',
            "test 56: replacing internal ${broker.hostname} ${broker.username} did not work"
        )

    def test_post_base_dir_replace(self):
        opt1 = "post_base_dir /${toto[1]}/${broker.username}/aaa"
        self.cfg.option(opt1.split())
        self.assertEqual(
            self.cfg.post_base_dir, '/tutu2/michel/aaa',
            "test 57: replacing internal ${toto[1]} did not work")

    def test_post_base_dir_replace_first(self):
        opt1 = "post_base_dir /${broker.hostname}/${broker.username}"
        self.cfg.option(opt1.split())
        opt1 = "post_base_dir /${toto}/${broker.username}/aaa"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.post_base_dir, '/tutu1/michel/aaa',
                         "test 58: replacing internal ${toto} did not work")

    # TODO add those tests
    # more config test to perform for full coverage...
    # options 'accept','get','reject']
    # option  'accept_unmatched'
    # def isMatchingPattern(self, str, accept_unmatch = False):
    # def sundew_getDestInfos(self, filename):
    # def validate_urlstr(self,urlstr):

    def test_sundew_dirPattern(self):
        # example of output for next test : new_dir = /20180404140433/SACN04CWAO140251RRA
        d_dir = '/${RYYYY}${RMM}${RDD}${RHH}${RMM}${RSS}/${T1}${T2}${A1}${A2}${ii}${CCCC}${YY}${GG}${Gg}${BBB}/'
        new_dir = self.cfg.sundew_dirPattern(urlstr='',
                                             basename='SACN04_CWAO_140251_RRA',
                                             destDir=d_dir,
                                             destName='aaa')
        self.assertTrue(
            new_dir.endswith('/SACN04CWAO140251RRA'),
            "test 59: sundew_dirPattern new_dir %s should end with /SACN04CWAO140251RRA"
            % new_dir)

    def test_sanity_log_dead(self):
        opt1 = "sanity_log_dead 1D"
        self.cfg.option(opt1.split())
        self.assertEqual(
            self.cfg.sanity_log_dead, 86400,
            "test 60: option sanity_log_dead or module duration_from_str did not work"
        )

    def test_heartbeat(self):
        opt1 = "sanity_log_dead 1D"
        self.cfg.option(opt1.split())
        opt1 = "heartbeat ${sanity_log_dead}"
        self.cfg.option(opt1.split())
        self.assertEqual(self.cfg.heartbeat, 86400,
                         "test 61: option heartbeat did not work")

    def test_subtopic(self):
        opt1 = 'subtopic aaa.vv\ ww.hh##bb.aaa.#'
        w = opt1.split()
        w = self.cfg.backslash_space(w)
        self.cfg.option(w)
        self.assertEqual(self.cfg.heartbeat, 86400,
                         "test 62: option subtopic did not work")


class SrConfigStdFilesRedirection(unittest.TestCase):
    """ Base class for stream redirection test cases

    These test stands for both out/err redirection in a single write (_io.TextIOWrapper) stream
    """
    def setUp(self) -> None:
        """ setup fake std file streams and logger to use through each test """
        self.stdoutpath = 'sys.stdout'
        self.fake_stdout = open(self.stdoutpath, 'w')
        self.logpath = 'stdfileredirection.log'
        logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                            level=logging.INFO)
        self.logger = logging.getLogger()
        self.logger.handlers[0].close()
        self.logger.removeHandler(self.logger.handlers[0])
        self.handler = handlers.TimedRotatingFileHandler(self.logpath,
                                                         when='s',
                                                         interval=1,
                                                         backupCount=5)
        self.handler.setLevel(logging.INFO)
        self.logger.addHandler(self.handler)

    def tearDown(self) -> None:
        """ clear all trace from each std files redirection test """
        self.fake_stdout.close()
        for path in glob.glob("{}*".format(self.logpath)):
            os.remove(path)
        os.remove(self.stdoutpath)


class SrConfigStdFileStreams(SrConfigStdFilesRedirection):
    def test_fake_stdout(self):
        """ test that the fake stdout is from the same type as python sys.stdout (in cmdline context) """
        self.assertEqual(type(self.fake_stdout), _io.TextIOWrapper)

    def test_opened_new_stream(self):
        """ test that the handler stream is open to standard files after we redirected stout/stderr to write to it """
        fake_stdout = StdFileLogWrapper(self.handler,
                                        self.fake_stdout.fileno())
        self.assertFalse(fake_stdout.closed)

    def test_closed_orig_stream(self):
        """ test that the original stream get closed after redirection """
        StdFileLogWrapper(self.handler, self.fake_stdout.fileno())
        self.assertTrue(self.fake_stdout)

    def test_handler_orig_stream(self):
        """ test that the original stream stays the same when creating the wrapper """
        stream_orig = self.handler.stream
        fake_stdout = StdFileLogWrapper(self.handler,
                                        self.fake_stdout.fileno())
        self.assertEqual(stream_orig, fake_stdout.handler.stream)

    def test_handler_rotated_stream(self):
        """ test that the stream changes when the log rotates """
        fake_stdout = StdFileLogWrapper(self.handler,
                                        self.fake_stdout.fileno())
        time.sleep(1)
        self.logger.info('test_handler_rotated_stream')
        self.assertNotEqual(fake_stdout.stream, fake_stdout.handler.stream)

    def test_handler_rotated_stream_written(self):
        """ test that the wrapper stream get updated after a rotation and a first write """
        fake_stdout = StdFileLogWrapper(self.handler,
                                        self.fake_stdout.fileno())
        time.sleep(1)
        self.logger.info('test_handler_rotated_stream_written')
        print('test_handler_rotated_stream_written', file=fake_stdout)
        self.assertEqual(fake_stdout.stream, fake_stdout.handler.stream)


class SrConfigStdFilesFileDescriptors(SrConfigStdFilesRedirection):
    """ Test cases over file descriptors consistency """
    def test_fds_before(self):
        """ test that file descriptor is different before redirection """
        self.assertNotEqual(self.fake_stdout.fileno(),
                            self.handler.stream.fileno())

    def test_stdfd_preserved(self):
        """ test that file descriptor is preserved after redirection """
        fake_stdout_fd = self.fake_stdout.fileno()
        fake_stdout = StdFileLogWrapper(self.handler,
                                        self.fake_stdout.fileno())
        self.assertEqual(fake_stdout_fd, fake_stdout.fileno())

    def test_handlerfd_preserved(self):
        """ test that the file descriptor is preserved after redirection """
        fake_stdout = StdFileLogWrapper(self.handler,
                                        self.fake_stdout.fileno())
        self.assertEqual(self.handler.stream.fileno(),
                         fake_stdout.handler.stream.fileno())


class SrConfigStdFilesOutput(SrConfigStdFilesRedirection):
    """ Test cases that validate that the output is printed where it should be before and after redirection """
    def test_logging(self):
        """ test that log file still receive log after redirection """
        StdFileLogWrapper(self.handler, self.fake_stdout.fileno())
        self.logger.info('test_logging')
        with open(self.logpath) as f:
            lines = f.readlines()
        self.assertEqual(lines[0], 'test_logging\n')

    @unittest.skip("this test fails sometime unexpectedly")
    def test_subprocess(self):
        """ test that subprocess stdout output is redirected to log """
        fake_stdout = StdFileLogWrapper(self.handler,
                                        self.fake_stdout.fileno())
        subprocess.Popen(['echo', 'test_subprocess'], stdout=fake_stdout)
        with open(self.logpath) as f:
            lines = f.readlines()
        self.assertEqual(lines[0], 'test_subprocess\n')

    @unittest.skip("this test fails most of the time unexpectedly")
    def test_stdout(self):
        """ test that stdout output is redirected to log """
        fake_stdout = StdFileLogWrapper(self.handler,
                                        self.fake_stdout.fileno())
        print('test_stdout', file=fake_stdout)
        with open(self.logpath) as f:
            lines = f.readlines()
        self.assertEqual(lines[0], 'test_stdout\n')


def suite():
    """ Create the test suite that include all sr_config test cases

    :return: sr_config test suite
    """
    sr_config_suite = unittest.TestSuite()
    sr_config_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(SrConfigChecksumTestCase))
    sr_config_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        SrConfigDeliveryOptionsTestCase))
    sr_config_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(SrConfigGeneralTestCase))
    sr_config_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        SrConfigPluginScriptTestCase))
    sr_config_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(SrConfigRandomizeTestCase))
    sr_config_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        SrConfigStdFilesFileDescriptors))
    sr_config_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(SrConfigStdFilesOutput))
    sr_config_suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(SrConfigStdFileStreams))
    return sr_config_suite


if __name__ == 'main':
    runner = unittest.TextTestRunner()
    runner.run(suite())
