#!/usr/bin/env python3

try:
    from sr_retry import *
except:
    from sarra.sr_retry import *

# ===================================
# self_test
# ===================================

failed = False


# test encode/decode
def test_retry_encode_decode(retry, message, done=False):

    if done: line = retry.msgToJSON(message, done)
    else: line = retry.msgToJSON(message)
    msg = retry.msgFromJSON(line)

    if msg.body != message.body:
        print("test 01: encode_decode body (done %s)" % done)
        failed = True

    if msg.delivery_info['exchange'] != message.delivery_info['exchange']:
        print("test 02: encode_decode exchange (done %s)" % done)
        failed = True

    if msg.delivery_info['routing_key'] != message.delivery_info['routing_key']:
        print("test 03: encode_decode routing_key (done %s)" % done)
        failed = True

    if not done:

        if msg.properties['application_headers']['my_header_attr'] != \
           message.properties['application_headers']['my_header_attr']:
            print("test 04: encode_decode headers (done %s)" % done)
            failed = True

    if done:

        if not '_retry_tag_' in msg.properties['application_headers']:
            print("encode_decode retry_tag not present")
            failed = True

        if '_retry_tag_' in msg.properties['application_headers'] and \
           msg.properties['application_headers']['_retry_tag_'] != 'done':
            print("encode_decode retry_tag != done")
            failed = True

        # test is_done

        if not retry.is_done(msg):
            print("encode_decode is_done method")
            failed = True

    return


# test is_expired methods
def test_retry_is_expired(retry, message):

    retry.retry_ttl = 100000

    if retry.is_expired(message):
        print("test 05: is_expired expires too soon ")
        failed = True

    time.sleep(1)
    retry.retry_ttl = 1

    if not retry.is_expired(message):
        print("test 06: is_expired should have expired ")
        failed = True

    retry.retry_ttl = 100000


# test msg_append_get_file
def test_retry_msg_append_get_file(retry, message):
    i = 0
    fp = None

    path = retry.retry_path

    while i < 100:
        i = i + 1
        r = i % 2

        message.body = '%s xyz://user@host /my/terrible/path%.10d' % (
            timeflt2str(time.time()), i)
        message.properties['application_headers']['sum'] = message.body

        # message to retry
        if r == 0:
            fp = retry.msg_append_to_file(fp, path, message)

            # message done
        else:
            fp = retry.msg_append_to_file(fp, path, message, True)

        try:
            del message.properties['application_headers']['_retry_tag_']
        except:
            pass

        # make sure close/append works for every entry
        fp.close()
        fp = None

    # test msg_get_from_file : read previous mixed message

    r = 0
    d = 0
    t = 0
    while True:

        fp, msg = retry.msg_get_from_file(fp, path)
        if not msg: break
        if retry.is_done(msg): d = d + 1
        else: r = r + 1
        t = t + 1

    if t != 100:
        print("test 07: append_get file incomplete (%d/100)" % t)
        failed = True

    if d != 50:
        print("test 08: append_get should have 50 done (%d/100)" % d)
        failed = True

    if r != 50:
        print("test 09: append_get should have 50 todo (%d/100)" % r)
        failed = True

    # at end file fp is none

    if fp != None:
        print(
            "test 10: append_get returned file pointer should have been None")
        failed = True

    os.unlink(path)


# test retry_get simple
def test_retry_get_simple(retry, message):

    # first case... retry.get with nothing

    if retry.get():
        print("test 11: append_get retry.get message should be None")
        failed = True

    # second case... retry.get with 3 retry messages

    fp = None
    path = retry.retry_path
    i = 0
    while i < 3:
        i = i + 1
        message.body = '%s xyz://user@host /my/terrible/path%.10d' % (
            timeflt2str(time.time()), i)
        message.properties['application_headers']['sum'] = message.body
        fp = retry.msg_append_to_file(fp, path, message)
    fp.close()

    # read them in
    t = 0
    while True:
        msg = retry.get()
        if not msg: break
        t = t + 1

    if t != 3:
        print("test 12: get simple problem reading 3 retry messages")
        failed = True

    if os.path.isfile(path):
        print("test 13: get simple complete reading implies unlink")
        failed = True


# overall case
def test_retry_overall(retry, message):

    # retry file has 10 messages...  half fails   ... and every 4 messages processed one new added
    # on_heartbeat every time needed

    # add 10 messages to retry file
    fp = None
    msg_count = 0
    while msg_count < 10:
        message.body = '%s xyz://user@host /my/terrible/path%.10d' % (
            timeflt2str(time.time()), msg_count)
        message.properties['application_headers']['sum'] = message.body
        fp = retry.msg_append_to_file(fp, retry.retry_path, message)
        msg_count = msg_count + 1
    fp.close()

    # read them with half success

    i = 0
    h_done = 1  # heartbeat done
    h_count = 0  # heartbeat count
    d_count = 0  # done      count
    f_count = 0  # failed    count
    while True:
        msg = retry.get()

        # heartbeat or done
        if not msg:
            if h_done: break
            retry.on_heartbeat(retry.parent)
            h_count = h_count + 1
            h_done = 1
            continue
        h_done = 0

        # processing another message
        i = i + 1

        # success or fail
        r = i % 2
        if r == 1:
            retry.add_msg_to_state_file(msg)
            f_count = f_count + 1
        else:
            retry.add_msg_to_state_file(msg, done=True)
            d_count = d_count + 1

        # every 4 success add a new retry
        r = i % 4
        if r == 0:
            try:
                del message.properties['application_headers']['_retry_tag_']
            except:
                pass
            message.body = '%s xyz://user@host /my/terrible/path%.10d' % (
                timeflt2str(time.time()), msg_count)
            message.properties['application_headers']['sum'] = message.body
            retry.add_msg_to_new_file(message)
            msg_count = msg_count + 1

    # msg_count != done d_count ...

    if msg_count != d_count:
        print("test 14: overall count failed msg_count %d  done_count %d ( failed %d, heartb %d)" % \
        (msg_count,d_count,f_count,h_count))
        failed = True

    if os.path.isfile(retry.retry_path):
        print(
            "test 15: overall retry_path completely read, should have been deleted"
        )
        failed = True


# ctrl_c case
def test_retry_ctrl_c(retry, message):

    # retry file has 10 messages...  half fails   ... and every 4 messages processed one new added
    # on_heartbeat every time needed

    # add 10 messages to retry file
    fp = None
    msg_count = 0
    while msg_count < 10:
        message.body = '%s xyz://user@host /my/terrible/path%.10d' % (
            timeflt2str(time.time()), msg_count)
        message.properties['application_headers']['sum'] = message.body
        fp = retry.msg_append_to_file(fp, retry.retry_path, message)
        msg_count = msg_count + 1
    fp.close()

    # read them with half success

    i = 0
    h_done = 1  # heartbeat done
    h_count = 0  # heartbeat count
    d_count = 0  # done      count
    f_count = 0  # failed    count
    a_count = 0  # added     count when 4  ctrl_c
    while True:
        msg = retry.get()

        # heartbeat or done
        if not msg:
            if h_done: break
            retry.on_heartbeat(retry.parent)
            h_count = h_count + 1
            h_done = 1
            continue
        h_done = 0

        # processing another message
        i = i + 1

        # success or fail
        r = i % 2
        if r == 1:
            retry.add_msg_to_state_file(msg)
            f_count = f_count + 1
        else:
            retry.add_msg_to_state_file(msg, done=True)
            d_count = d_count + 1

        # every 4 success add a new retry
        r = i % 4
        if r == 0:
            try:
                del message.properties['application_headers']['_retry_tag_']
            except:
                pass
            message.body = '%s xyz://user@host /my/terrible/path%.10d' % (
                timeflt2str(time.time()), msg_count)
            message.properties['application_headers']['sum'] = message.body
            retry.add_msg_to_new_file(message)
            msg_count = msg_count + 1
            a_count = a_count + 1
            if a_count == 2: break

    # ctrl_c heartbeat

    retry.close()
    retry.on_heartbeat(retry.parent)

    # start same loop
    while True:
        msg = retry.get()

        # heartbeat or done
        if not msg:
            if h_done: break
            retry.on_heartbeat(retry.parent)
            h_count = h_count + 1
            h_done = 1
            continue
        h_done = 0

        # processing another message
        i = i + 1

        # success or fail
        r = i % 2
        if r == 1:
            retry.add_msg_to_state_file(msg)
            f_count = f_count + 1
        else:
            retry.add_msg_to_state_file(msg, done=True)
            d_count = d_count + 1

        # every 4 success add a new retry
        r = i % 4
        if r == 0:
            try:
                del message.properties['application_headers']['_retry_tag_']
            except:
                pass
            message.body = '%s xyz://user@host /my/terrible/path%.10d' % (
                timeflt2str(time.time()), msg_count)
            message.properties['application_headers']['sum'] = message.body
            retry.add_msg_to_new_file(message)
            msg_count = msg_count + 1

    # msg_count != done d_count ...

    if msg_count != d_count:
        print("test 16: ctrl_c count failed msg_count %d  done_count %d ( failed %d, heartb %d)" % \
        (msg_count,d_count,f_count,h_count))
        failed = True

    if os.path.isfile(retry.retry_path):
        print(
            "test 17: ctrl_c retry_path completely read, should have been deleted"
        )
        failed = True


def self_test():

    retry_path = '/tmp/retry'
    try:
        os.unlink(retry_path)
    except:
        pass
    try:
        os.unlink(retry_path + '.new')
    except:
        pass
    try:
        os.unlink(retry_path + '.state')
    except:
        pass
    try:
        os.unlink(retry_path + '.heart')
    except:
        pass

    #setup retry parent
    cfg = sr_config()
    cfg.configure()
    cfg.retry_path = retry_path
    cfg.option(['ll', 'None'])

    message = raw_message(cfg.logger)

    message.pubtime = timeflt2str(time.time())
    message.baseurl = "xyz://user@host"
    message.relpath = '/my/terrible/path%.10d' % 0
    notice = '%s %s %s' % (message.pubtime, message.baseurl, message.relpath)

    headers = {}
    headers['sum'] = notice
    headers['my_header_attr'] = 'my_header_attr_value'

    message.delivery_info['exchange'] = cfg.exchange
    message.delivery_info['routing_key'] = 'my_topic'
    message.properties['application_headers'] = headers
    message.body = notice

    now = time.time()

    retry = sr_retry(cfg)

    # test encode decode methods

    test_retry_encode_decode(retry, message)
    test_retry_encode_decode(retry, message, done=True)

    # test is_expired methods

    test_retry_is_expired(retry, message)

    # test msg_append_to_file : write 100 message to a file

    test_retry_msg_append_get_file(retry, message)

    # test get simplest cases

    test_retry_get_simple(retry, message)

    # test complex case no interrup

    test_retry_overall(retry, message)

    # test ctrl_c

    test_retry_ctrl_c(retry, message)

    # test close

    retry.close()
    e = time.time() - now

    # performance test

    json_line = '["v02.post.sent_by_tsource2send", {"atime": "20180118151049.356378078", "from_cluster": "localhost", "mode": "644", "mtime": "20180118151048", "parts": "1,69,1,0,0", "source": "tsource", "sum": "d,c35f14e247931c3185d5dc69c5cd543e", "to_clusters": "localhost"}, "20180118151050.45 ftp://anonymous@localhost:2121 /sent_by_tsource2send/SXAK50_KWAL_181510___58785"]'

    i = 0
    top = 100000
    now = time.time()
    while i < top:
        i = i + 1
        topic, headers, notice = json.loads(json_line)
        json_line = json.dumps([topic, headers, notice], sort_keys=True)

    e = time.time() - now

    retry.message.delivery_info['exchange'] = "test"
    retry.message.delivery_info['routing_key'] = topic
    retry.message.properties['application_headers'] = headers
    retry.message.body = notice

    (retry.message.pubtime, retry.message.baseurl,
     retry.message.relpath) = notice.split()

    i = 0
    now = time.time()
    while i < top:
        i = i + 1
        line = retry.msgToJSON(message)
        msg = retry.msgFromJSON(line)

    e = time.time() - now

    i = 0
    now = time.time()
    while i < top:
        i = i + 1
        line = retry.msgToJSON(message, True)
        msg = retry.msgFromJSON(line)
        del msg.properties['application_headers']['_retry_tag_']

    e = time.time() - now

    fp = None
    path = "/tmp/ftest1"
    try:
        os.unlink(path)
    except:
        pass

    i = 0
    now = time.time()
    while i < top:
        i = i + 1
        fp = retry.msg_append_to_file(fp, path, message)
    fp.close()

    e = time.time() - now

    if not failed:
        print("sr_retry.py TEST PASSED")
    else:
        print("sr_retry.py TEST FAILED")
        sys.exit(1)


# ===================================
# MAIN
# ===================================


def main():
    try:
        self_test()
    except:
        print("sr_retry.py TEST FAILED")
        raise


# =========================================
# direct invocation : self testing
# =========================================

if __name__ == "__main__":
    main()
