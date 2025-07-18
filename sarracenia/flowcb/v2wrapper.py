from base64 import b64decode, b64encode
from codecs import decode, encode

import copy
import logging
from hashlib import md5
from hashlib import sha512
import os
import sarracenia.config
import time
import types
import urllib

import sarracenia
from sarracenia.flowcb import FlowCB

from sarracenia import nowflt, timestr2flt, timev2tov3str

logger = logging.getLogger(__name__)

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

sum_algo_v2tov3 = { v: k for k,v in sum_algo_v3tov2.items() }

def sumstrFromMessage( msg ) -> str:
    """
   accepts a v3 message as argument msg. returns the corresponding sum string for a v2 'sum' header.
    """

    if 'identity' in msg:
        if msg['identity']['method'] in sum_algo_v3tov2:
           sa = sum_algo_v3tov2[msg["identity"]["method"]]
        else: # FIXME ... 1st md5name case... default when unknown...
           logger.error('identity method unknown to v2: %s, replacing with md5name' % msg['identity']['method'] )
           sa = 'n'
           sv = md5(bytes(os.path.basename(msg['relPath']),'utf-8')).hexdigest()

        # transform sum value
        if sa in ['0', 'a']:
            sv = msg["identity"]["value"]
        elif sa in ['z']:
            sv = sum_algo_v3tov2[msg["identity"]["value"]]
        else:
            sv = encode(
                decode(msg["identity"]["value"].encode('utf-8'), "base64"),
                'hex').decode('utf-8')
        sumstr = sa + ',' + sv
    else:
        # FIXME ... 2nd md5name case.
        sumstr = 'n,%s' % md5(bytes(os.path.basename(msg['relPath']),'utf-8')).hexdigest()

    if 'fileOp' in msg:
        if 'rename' in msg['fileOp']:
            msg['oldname'] = msg['fileOp']['rename']

        if 'link' in msg['fileOp']:
            hash = sha512()
            hash.update( bytes( msg['fileOp']['link'], encoding='utf-8' ) )
            sumstr = 'L,%s' % hash.hexdigest()
        elif 'remove' in msg['fileOp']:
            hash   = sha512()
            hash.update(bytes(os.path.basename(msg['relPath']), encoding='utf-8'))
            sumstr = 'R,%s' % hash.hexdigest()
        elif 'directory' in msg['fileOp']:
            hash   = sha512()
            hash.update(bytes(os.path.basename(msg['relPath']), encoding='utf-8'))

            if 'remove' in msg['fileOp']:
                sumstr = 'r,%s' % hash.hexdigest()
            else:
                sumstr = 'm,%s' % hash.hexdigest()
        else:
            logger.error('unknown fileOp: %s' % msg['fileOp'] )
    return sumstr

class Message:
    def __init__(self, h):
        """
         builds the in-memory representation of a message as expected by v2 plugins.
         In v3, a message is just a dictionary. in v2 it is an object.

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
            if 'number' in p:
                remainder = p['manifest'][p['number']]['size']
                number = p['number']
            else:
                number=0
                if 'manifest' in p:
                    remainder = p['manifest'][len(p['manifest'])-1]['size']
                else:       
                    remainder = 0
            h['parts'] = '%s,%d,%d,%d,%d' % (m, p['size'], len(p['manifest']),
                                             remainder, number)

        h['topic'] = [ 'v02', 'post' ] + self.relpath.split('/')[0:-1]

        if 'parts' in h:
            self.partstr = h['parts']
        #else:
        #    self.partstr = None

        self.sumstr = sumstrFromMessage( h )
        self.sumflg = self.sumstr[0]
        h['sum'] = self.sumstr

        if 'fileOp' in h and  'rename' in h['fileOp'] :
            h['oldname'] = h['fileOp']['rename'] 
       
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

    def set_parts(self):
        logger.info("set_parts not implemented")
        pass


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

        """
        global logger

        logging.basicConfig(format=o.logFormat,
                            level=getattr(logging, o.logLevel.upper()))

        logger.setLevel(getattr(logging, o.logLevel.upper()))

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

        if hasattr(o, 'no'):
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

        c1 = set(vars(self))

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

        c2 = set(vars(self))
        c12diff = list(c2 - c1)
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
            try:
                if self.run_entry('on_message', m):
                    outgoing.append(m)
                else:
                    worklist.rejected.append(m)
            except Exception as Ex:
               logger.error( f"plugin {m} died: {Ex}" );
               logger.debug( 'details: ', exc_info=True)
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
        self.on_time('on_heartbeat')

    def on_start(self):
        self.on_time('on_start')

    def on_stop(self):
        self.on_time('on_stop')

    def restoreMsg(self, m, v2msg):

        if 'topic' in m:
            if m['topic'][0:2] == ['v02', 'post' ]:
               m['topic'] = self.o.post_topicPrefix + m['topic'][2:]      

        if ('link' in v2msg.headers):
            if not 'fileOp' in m:
               m['fileOp'] = {}

            if m['fileOp']['link'] != v2msg.headers['link']:
                m['fileOp']['link'] = v2msg.headers['link']
            
        for h in ['oldname', 'newname' ]:
            if (h in v2msg.headers) and ((h not in m) or
                                         (v2msg.headers[h] != m[h])):
                m[h] = v2msg.headers[h]

        if v2msg.new_dir != m['new_dir']:
            m['new_dir'] = v2msg.new_dir
            relpath = m['new_dir'] + '/' + v2msg.new_file
            if self.o.post_baseDir:
                relpath = relpath.replace(self.o.post_baseDir, '', 1)
            m['new_relPath'] = relpath

        if v2msg.baseurl != m['baseUrl']:
            m['baseUrl'] = v2msg.baseurl

        if hasattr(v2msg, 'new_file'):
            if ('new_file' not in m) or (m['new_file'] != v2msg.new_file):
                m['new_file'] = v2msg.new_file

        if hasattr(
                v2msg,
                'post_base_dir') and (v2msg.post_base_dir != m['new_baseDir']):
            m['post_baseDir'] = v2msg.post_base_dir

    def run_entry(self, ep, m):
        """
           run plugins for a given entry point.
        """
        self.msg = Message(m)
        self.msg.topic = '.'.join(self.o.topicPrefix + m['subtopic'])
        self.o.msg = self.msg
        if hasattr(self.msg, 'partstr'):
            self.o.partstr = self.msg.partstr
        self.o.sumstr = self.msg.sumstr

        varsb4 = set(vars(self.msg))

        for opt in self.state_vars:
            if hasattr(self.o, opt):
                setattr(self.msg, opt, getattr(self.o, opt))

        ok = True
        for plugin in self.v2plugins[ep]:
            ok = plugin(self.o)
            if not ok: break

        vars_after = set(vars(self.msg))

        self.restoreMsg(m, self.msg)

        diff = list(vars_after - varsb4)
        if len(diff) > 0:
            self.state_vars.extend(diff)

        return ok
