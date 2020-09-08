#!/usr/bin/env python3

try:
    from sr_consumer import *
except:
    from sarra.sr_consumer import *

# ===================================
# self_test
# ===================================


def self_test():

    failed = False

    opt1 = 'accept .*bulletins.*'
    opt2 = 'reject .*'
    opt3 = 'll None'

    #setup consumer to catch first post
    cfg = sr_config()
    cfg.configure()

    cfg.load_sums()
    cfg.broker = urllib.parse.urlparse(
        "amqps://anonymous:anonymous@hpfx.collab.science.gc.ca")
    #cfg.broker         = urllib.parse.urlparse("amqps://anonymous:anonymous@dd.weather.gc.ca")
    cfg.prefetch = 10
    cfg.bindings = [('xpublic', 'v02.post.#')]
    cfg.durable = False
    cfg.expire = 300 * 1000  # 5 mins = 300 secs
    cfg.message_ttl = 300 * 1000  # 5 mins = 300 secs
    cfg.user_cache_dir = os.getcwd()
    cfg.config_name = "test"
    cfg.queue_name = None
    cfg.retry_path = '/tmp/retry'
    cfg.option(opt1.split())
    cfg.option(opt2.split())
    cfg.option(opt3.split())

    consumer = sr_consumer(cfg)

    # loop 10000 times to try to catch a bulletin

    i = 0
    while True:
        ok, msg = consumer.consume()
        if ok: break

        i = i + 1
        if i == 10000:
            msg = None
            break

    os.unlink(consumer.queuepath)

    consumer.cleanup()

    if msg == None:
        print("test 01: sr_consumer TEST Failed no message")
        failed = True

    elif not 'bulletins' in msg.notice:
        print("test 02: sr_consumer TEST Failed not a bulletin")
        failed = True

    if not failed:
        print("sr_consumer.py TEST PASSED")
    else:
        print("sr_consumer.py TEST FAILED")
        sys.exit(1)


# ===================================
# MAIN
# ===================================


def main():
    try:
        self_test()
    except:
        print("sr_consumer.py TEST FAILED")
        raise


# =========================================
# direct invocation : self testing
# =========================================

if __name__ == "__main__":
    main()
