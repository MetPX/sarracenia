import logging
import os
import sys
import unittest
import tests.unit_tests.sr_config_unit_test as cfg_tests

from sarra.sr_subscribe import sr_subscribe


class OptionsTestCase(unittest.TestCase):
    def test_default_boolean_value(self):
        subscriber = sr_subscribe()
        subscriber.configure()
        subscriber.overwrite_defaults()
        for option_tuple in cfg_tests.list_options(r'.*?boolean.*?'):
            name = option_tuple[0]
            default_value = option_tuple[3]
            removed = option_tuple[4]
            with self.subTest('test_{}'.format(name)):
                if removed:
                    self.skipTest('Option has been removed')
                if name == 'debug':
                    self.assertEqual(subscriber.loglevel, logging.INFO)
                elif name == 'xattr_disable':
                    self.assertEqual(cfg_tests.xattr_disabled, subscriber.isTrue(default_value.strip()))
                elif name == 'suppress_duplicates':
                    self.assertFalse(subscriber.caching)
                else:
                    self.assertEqual(getattr(subscriber, name), subscriber.isTrue(default_value.strip()))


# ===================================
# self test
# ===================================

class test_logger:
    def silence(self, str):
        pass

    def __init__(self):
        self.debug = print
        self.error = print
        self.info = print
        self.warning = print
        self.debug = self.silence
        self.info = self.silence


def test_sr_subscribe():
    logger = test_logger()

    opt1 = 'on_message ./on_msg_test.py'
    opt2 = 'on_part ./on_prt_test.py'
    opt3 = 'on_file ./on_fil_test.py'

    # here an example that calls the default_on_message...
    # then process it if needed
    f = open("./on_msg_test.py", "w")
    f.write("class Transformer(object): \n")
    f.write("      def __init__(self):\n")
    f.write("          self.count_ok = 0\n")
    f.write("      def perform(self, parent ):\n")
    f.write("          if parent.msg.sumflg == 'R' : return True\n")
    f.write("          self.count_ok += 1\n")
    f.write("          parent.msg.mtype_m = self.count_ok\n")
    f.write("          return True\n")
    f.write("transformer = Transformer()\n")
    f.write("self.on_message = transformer.perform\n")
    f.close()

    f = open("./on_prt_test.py", "w")
    f.write("class Transformer(object): \n")
    f.write("      def __init__(self): \n")
    f.write("          self.count_ok = 0\n")
    f.write("      def perform(self, parent ):\n")
    f.write("          if parent.msg.sumflg == 'R' : return True\n")
    f.write("          self.count_ok += 1\n")
    f.write("          parent.msg.mtype_p = self.count_ok\n")
    f.write("          return True\n")
    f.write("transformer = Transformer()\n")
    f.write("self.on_part = transformer.perform\n")
    f.close()

    f = open("./on_fil_test.py", "w")
    f.write("class Transformer(object): \n")
    f.write("      def __init__(self): \n")
    f.write("          self.count_ok = 0\n")
    f.write("      def perform(self, parent ):\n")
    f.write("          self.count_ok += 1\n")
    f.write("          parent.msg.mtype_f  = self.count_ok\n")
    f.write("          return True\n")
    f.write("transformer = Transformer()\n")
    f.write("self.on_file = transformer.perform\n")
    f.close()

    # setup sr_subscribe (just this instance)

    subscribe = sr_subscribe()
    subscribe.logger = logger

    # set options
    subscribe.option(opt1.split())
    subscribe.option(opt2.split())
    subscribe.option(opt3.split())
    subscribe.loglevel = logging.DEBUG
    subscribe.setlog()

    # ==================
    # set instance

    subscribe.instance = 1
    subscribe.nbr_instances = 1
    subscribe.connect()

    # do an empty consume... assure AMQP's readyness

    # process with our on_message and on_post
    # expected only 1 hit for a good message
    # to go to xreport

    i = 0
    j = 0
    k = 0
    c = 0
    while True:
        ok, msg = subscribe.consumer.consume()
        if not ok: continue
        ok = subscribe.process_message()
        if not ok: continue
        if subscribe.msg.mtype_m == 1: j += 1
        if subscribe.msg.mtype_f == 1: k += 1
        logger.debug(" new_file = %s" % msg.new_file)
        subscribe.msg.sumflg = 'R'
        subscribe.msg.checksum = '0'
        ok = subscribe.process_message()

        i = i + 1
        if i == 1: break

    subscribe.close()

    if j != 1 or k != 1:
        print("sr_subscribe TEST Failed 1")
        sys.exit(1)

    # FIX ME part stuff
    # with current message from a local file
    # create some parts in parent.msg
    # and process them with subscribe.process_message
    # make sure temporary redirection, insert, download inplace
    # truncate... etc works

    print("sr_subscribe TEST PASSED")

    os.unlink('./on_fil_test.py')
    os.unlink('./on_msg_test.py')
    os.unlink('./on_prt_test.py')

    sys.exit(0)


def suite():
    """ Create the test suite that include all sr_config test cases

    :return: sr_config test suite
    """
    sr_config_suite = unittest.TestSuite()
    sr_config_suite.addTests(unittest.TestLoader().loadTestsFromTestCase(OptionsTestCase))
    return sr_config_suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.run(suite())
