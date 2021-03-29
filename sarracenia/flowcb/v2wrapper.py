from base64 import b64decode, b64encode
from codecs import decode, encode

import copy
import logging
import os
import sarracenia.config
import time
import types
import urllib

import sarracenia
from sarracenia.flowcb import FlowCB

from sarracenia import nowflt, timestr2flt, timev2tov3str

logger = logging.getLogger(__name__)


class Message:
    def __init__(self, h):
        """
         in v3, a message is just a dictionary. in v2 it is an object.
         build from sr_message.

         assign everything, except topic... because the topic is stored outside the body in v02.
        """

        self.pubtime = h['pubTime'].replace("T", "")
        self.baseurl = h['baseUrl']
        self.relpath = h['relPath']

        if 'new_dir' in h:
            self.new_dir = h['new_dir']
            self.new_file = h['new_file']

        if 'new_relPath' in h:
            self.new_relpath = h['new_relPath']

        self.urlstr = self.baseurl + self.relpath
        self.url = urllib.parse.urlparse(self.urlstr)

        self.notice = self.pubtime + ' ' + h["baseUrl"] + ' ' + h[
            "relPath"].replace(' ', '%20').replace('#', '%23')

        #FIXME: ensure headers are < 255 chars.
        for k in ['mtime', 'atime']:
            if k in h:
                h[k] = h[k].replace("T", "")

        #FIXME: sum header encoding.
        if 'size' in h:
            if type(h['size']) is str:
                h['size'] = int(h['size'])
            h['parts'] = '1,%d,1,0,0' % h['size']

        if 'blocks' in h:
            if h['blocks']['method'] == 'inplace':
                m = 'i'
            else:
                m = 'p'
            p = h['blocks']
            h['parts'] = '%s,%d,%d,%d,%d' % (m, p['size'], p['count'],
                                             p['remainder'], p['number'])

        if 'parts' in h:
            self.partstr = h['parts']
        #else:
        #    self.partstr = None

        if 'integrity' in h:
            sum_algo_v3tov2 = {
                "arbitrary": "a",
                "md5": "d",
                "sha512": "s",
                "md5name": "n",
                "random": "0",
                "link": "L",
                "remove": "R",
                "cod": "z"
            }
            sa = sum_algo_v3tov2[h["integrity"]["method"]]

            self.sumflag = sa
            # transform sum value
            if sa in ['0']:
                sv = h["integrity"]["value"]
            elif sa in ['z']:
                sv = sum_algo_v3tov2[h["integrity"]["value"]]
            else:
                sv = encode(
                    decode(h["integrity"]["value"].encode('utf-8'), "base64"),
                    'hex').decode('utf-8')
            h["sum"] = sa + ',' + sv
            self.sumflg = sa
            self.sumstr = h["sum"]
        else:
            self.sumstr = None
            self.sumflg = None

        self.headers = h
        self.hdrstr = str(h)
        self.isRetry = False

        # from sr_message/sr_new ...
        self.local_offset = 0
        self.in_partfile = False
        self.local_checksum = None

        self.target_file = None
        # does not cover partitioned files.

    def set_hdrstr(self):
        logger.info("set_hdrstr not implemented")
        pass

    def get_elapse(self):
        return nowflt() - timestr2flt(self.pubtime)

    def set_parts():
        logger.info("set_parts not implemented")
        pass


def v02tov03message(body, headers, topic, topicPrefix):
    msg = headers
    msg['subtopic'] = topic.split('.')[len(topicPrefix):]
    if not '_deleteOnPost' in msg:
        msg['_deleteOnPost'] = set()
    msg['_deleteOnPost'] |= set(['subtopic'])

    pubTime, baseUrl, relPath = body.split(' ')[0:3]
    msg['pubTime'] = timev2tov3str(pubTime)
    msg['baseUrl'] = baseUrl.replace('%20', ' ').replace('%23', '#')
    msg['relPath'] = relPath
    for t in ['atime', 'mtime']:
        if t in msg:
            msg[t] = timev2tov3str(msg[t])

    if 'sum' in msg:
        sum_algo_map = {
            "a": "arbitrary",
            "d": "md5",
            "s": "sha512",
            "n": "md5name",
            "0": "random",
            "L": "link",
            "R": "remove",
            "z": "cod"
        }
        sm = sum_algo_map[msg["sum"][0]]
        if sm in ['random']:
            sv = msg["sum"][2:]
        elif sm in ['cod']:
            sv = sum_algo_map[msg["sum"][2:]]
        else:
            sv = encode(decode(msg["sum"][2:], 'hex'),
                        'base64').decode('utf-8').strip()
        msg["integrity"] = {"method": sm, "value": sv}
        del msg['sum']

    if 'parts' in msg:
        (style, chunksz, block_count, remainder,
         current_block) = msg['parts'].split(',')
        if style in ['i', 'p']:
            msg['blocks'] = {}
            msg['blocks']['method'] = {
                'i': 'inplace',
                'p': 'partitioned'
            }[style]
            msg['blocks']['size'] = int(chunksz)
            msg['blocks']['count'] = int(block_count)
            msg['blocks']['remainder'] = int(remainder)
            msg['blocks']['number'] = int(current_block)
        else:
            msg['size'] = int(chunksz)
        del msg['parts']

    return msg


class V2Wrapper(FlowCB):
    def __init__(self, o):
        """
           A wrapper class to run v02 plugins.
           us run_entry(entry_point,module)

           entry_point is a string like 'on_message',  and module being the one to add.

           weird v2 stuff:   
                when calling init, self is a config/subscriber...
                when calling on_message, self is a message...
                that is kind of blown away for each message...
                parent is the config/subscriber in both cases.
                so v2 state variables are always stored in parent.

           FIXME V2 Do_* not done.
           this is good for on_* plugins.  noticed a wrinkle for do_* plugins, where a 'registered_as' routine is needed.
           and do_* are registered "pre protocol" (that is, for each protocol they claim via registered_as)
           This is not taken care of yet.

        """
        global logger

        logging.basicConfig(format=o.logFormat,
                            level=getattr(logging, o.logLevel.upper()))

        logger.setLevel( getattr(logging, o.logLevel.upper()))

        #logger.info('logging: fmt=%s, level=%s' % ( o.logFormat, o.logLevel ) )

        # FIXME, insert parent fields for v2 plugins to use here.
        self.logger = logger
        #logger.info('v2wrapper init start')

        self.state_vars = []

        if o.statehost:
            hostdir = o.hostdir
        else:
            hostdir = None

        self.user_cache_dir = sarracenia.config.get_user_cache_dir(hostdir)

        if hasattr(o,'no') :
            self.instance = o.no
        else:
            self.instance = 0

        self.o = o

        self.v2plugins = {}
        self.consumer = types.SimpleNamespace()
        self.consumer.sleep_min = 0.01

        for ep in sarracenia.config.Config.v2entry_points:
            self.v2plugins[ep] = []

        unsupported_v2_events = ['do_download', 'do_get', 'do_put', 'do_send']
        for e in o.v2plugins:
            #logger.info('resolving: %s' % e)
            for v in o.v2plugins[e]:
                if e in unsupported_v2_events:
                    logger.error(
                        'v2 plugin conversion required, %s too different in v3'
                        % e)
                    continue
                self.add(e, v)

        #propagate options back to self.o for on_timing calls.
        #for v2o in self.o.v2plugin_options:
        #    setattr( self.o, v2o, getattr(self,v2o )  )

        # backward compat...
        self.o.user_cache_dir = self.o.cfg_run_dir
        self.o.instance = self.instance
        self.o.logger = self.logger
        if hasattr(self.o, 'post_baseDir'):
            self.o.post_base_dir = self.o.post_baseDir

        #logger.info('v2wrapper init done')

    def declare_option(self, option):
        logger.info('v2plugin option: %s declared' % option)

        self.state_vars.append(option)

        self.o.add_option(option)
        if not hasattr(self.o, option):
            logger.info('value of %s not set' % option)
            return

        if type(getattr(self.o, option)) is not list:
            setattr(self.o, option, [getattr(self.o, option)])

    def add(self, opname, path):

        setattr(self, opname, None)

        if path == 'None' or path == 'none' or path == 'off':
            logger.info("Reset plugin %s to None" % opname)
            exec('self.' + opname + '_list = [ ]')
            return True

        ok, script = sarracenia.config.config_path('plugins',
                                                   path,
                                                   mandatory=True,
                                                   ctype='py')
        if not ok:
            logger.error("installing %s %s failed: not found " %
                         (opname, path))
            return False

        #logger.info('installing: %s %s' % ( opname, path ) )

        c1 = copy.deepcopy(vars(self))

        try:
            with open(script) as f:
                exec(
                    compile(f.read().replace('self.plugin', 'self.v2plugin'),
                            script, 'exec'))
        except:
            logger.error(
                "sr_config/execfile 2 failed for option '%s' and plugin '%s'" %
                (opname, path))
            logger.debug('Exception details: ', exc_info=True)
            return False

        if opname == 'plugin':
            if getattr(self, 'v2plugin') is None:
                logger.error("%s plugin %s incorrect: does not set self.%s" %
                             ('v2plugin', path, 'v2plugin'))
                return False

            # pci plugin-class-instance... parent is self (a v2wrapper)
            pci = self.v2plugin.lower()
            s = pci + ' = ' + self.v2plugin + '(self)'
            exec(pci + ' = ' + self.v2plugin + '(self)')
            s = 'vars(' + self.v2plugin + ')'
            pcv = eval('vars(' + self.v2plugin + ')')
            for when in sarracenia.config.Config.v2entry_points:
                if when in pcv:
                    #logger.info("v2 registering %s from %s" % ( when, path ) )

                    # 2020/05/22. I think the commented exec can be removed.
                    #FIXME: this breaks things horrible in v3. I do not see the usefulness even in v2.
                    #       everything is done with the lists, so value of setting individual value is nil.
                    #      self.on_start... vs.
                    #       self.v2plugins['on_start'].append( thing. )
                    #exec( 'self.' + when + '=' + pci + '.' + when )
                    eval('self.v2plugins["' + when + '"].append(' + pci + '.' +
                         when + ')')
        else:
            if getattr(self, opname) is None:
                logger.error("%s plugin %s incorrect: does not set self.%s" %
                             (opname, path, opname))
                return False

            #eval( 'self.' + opname + '_list.append(self.' + opname + ')' )
            eval('self.v2plugins["' + opname + '"].append( self.' + opname +
                 ')')

        c2 = vars(self)
        c12diff = list(set(c2) - set(c1))
        #logger.error('init added: +%s+ to %s' % (c12diff, self.state_vars) )
        if len(c12diff) > 0:
            self.state_vars.extend(c12diff)

        for opt in self.state_vars:
            if hasattr(self, opt):
                setattr(self.o, opt, getattr(self, opt))

        return True

    def after_work(self, worklist):
        ok_to_post = []
        for m in worklist.ok:
            if self.run_entry('on_file', m):
                ok_to_post.append(m)
            else:
                #worklist.failed.append(m)
                pass
                # FIXME: what should we do on failure of on_file plugin?
                #     download worked, but on_file failed... hmm...

        worklist.ok = ok_to_post

        outgoing = []
        for m in worklist.ok:
            if self.run_entry('on_post', m):
                outgoing.append(m)
            else:
                worklist.rejected.append(m)
        # set incoming for future steps.
        worklist.ok = outgoing


    def after_accept(self, worklist):

        outgoing = []
        for m in worklist.incoming:
            if self.run_entry('on_message', m):
                outgoing.append(m)
            else:
                worklist.rejected.append(m)
        # set incoming for future steps.
        worklist.incoming = outgoing

    def on_time(self, time):
        """
           run plugins for a given entry point.
        """
        logger.info('v2 run %s' % time)
        for plugin in self.v2plugins[time]:
            plugin(self.o)

    def on_housekeeping(self):
        self.on_time('on_housekeeping')

    def on_start(self):
        self.on_time('on_start')

    def on_stop(self):
        self.on_time('on_stop')

    def restoreMsg(self, m, v2msg):

        for h in ['oldname', 'newname', 'link']:
            if (h in v2msg.headers) and ((h not in m) or
                                         (v2msg.headers[h] != m[h])):
                m[h] = v2msg.headers[h]

        for h in ['new_file', 'new_dir']:
            if hasattr(v2msg, h):
                if (h in m) and (getattr(v2msg, h) != m[h]):
                    m[h] = getattr(v2msg, h)

        if v2msg.baseurl != m['baseUrl']:
            m['baseUrl'] = v2msg.baseurl

        if hasattr(v2msg,
                   'new_relpath') and (v2msg.new_relpath != m['new_relPath']):
            m['new_relPath'] = v2msg.new_relpath

        if hasattr(
                v2msg,
                'post_base_dir') and (v2msg.post_base_dir != m['new_baseDir']):
            m['post_baseDir'] = v2msg.post_base_dir

    def run_entry(self, ep, m):
        """
           run plugins for a given entry point.
        """
        self.msg = Message(m)
        self.msg.topic = '.'.join( self.o.topicPrefix + m['subtopic'] )
        self.o.msg = self.msg
        if hasattr(self.msg, 'partstr'):
            self.o.partstr = self.msg.partstr
        self.o.sumstr = self.msg.sumstr

        varsb4 = copy.deepcopy(vars(self.msg))

        for opt in self.state_vars:
            if hasattr(self.o, opt):
                setattr(self.msg, opt, getattr(self.o, opt))

        ok = True
        for plugin in self.v2plugins[ep]:
            ok = plugin(self.o)
            if not ok: break

        vars_after = vars(self.msg)

        self.restoreMsg(m, self.msg)

        diff = list(set(vars_after) - set(varsb4))
        if len(diff) > 0:
            self.state_vars.extend(diff)

        return ok
