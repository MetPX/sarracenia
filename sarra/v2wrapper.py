
import logging
import os
import sarra.config
import time
import types

from abc import ABCMeta, abstractmethod

from sarra.sr_util import nowflt

logger = logging.getLogger( __name__ )

class Message:

    def __init__(self, h):
        """
         in v3, a message is just a dictionary. in v2 it is an object.
         build from sr_message.
        """
        # FIXME: new_dir, new_file
        # FIXME: sumstr, partstr, 
        # FIXME: url (result of urlparse?)
        # FIXME: headers

        self.pubtime=h['pubTime'].replace("T","")
        self.baseurl=v3m['baseURL']
        self.relpath=v3m['relPath']

        self.notice=self.pubtime + ' ' + h["baseURL" ] + ' ' + h["relPath"]
        del h["pubTime"]
        del h["baseURL"]
        del h["relPath"]

        #FIXME: ensure headers are < 255 chars.
        for k in [ 'mtime', 'atime' ]:
            h[ k ] = h[k].replace("T","")

        #FIXME: sum header encoding.
        if 'size' in h:
            h[ 'parts' ] = '1,%d,1,0,0' % h['size']
            del h['size']

        if 'blocks' in h:
            if h['parts'] == 'inplace': 
                m='i'
            else: 
                m='p'
            p=h['blocks']
            h[ 'parts' ] = '%s,%d,%d,%d,%d' % ( m, p['size'], p['count'], 
                  p['remainder'], p['number'] )
            del h['blocks']

        if 'content' in h:  #v02 does not support inlining
            del h['content']

        if 'integrity' in h:
            sum_algo_v3tov2 = { "arbitrary":"a", "md5":"d", "sha512":"s", 
                "md5name":"n", "random":"0", "link":"L", "remove":"R", "cod":"z" }
            sa = sum_algo_v3tov2[ self.headers[ "integrity" ][ "method" ] ]

            # transform sum value
            if sa in [ '0' ]:
                sv = self.headers[ "integrity" ][ "value" ]
            elif sa in [ 'z' ]:
                sv = sum_algo_v3tov2[ self.headers[ "integrity" ][ "value" ] ]
            else:
                sv = encode( decode( self.headers[ "integrity" ][ "value" ].encode('utf-8'), "base64" ), 'hex' )
            h[ "sum" ] = sa + ',' + sv
            del h['integrity']

        self.headers=h


    def get_elapse():
        pass

    def set_parts():
        pass

def v02tov03message( body, headers, topic ):
        msg = headers
        msg[ 'topic' ] = topic
        pubtime, baseurl, relpath = body.split(' ')[0:3]
        msg[ 'pubTime' ] = timev2tov3str( pubtime )
        msg[ 'baseUrl' ] = baseurl
        msg[ 'relPath' ] = relPath
        for t in [ 'atime', 'mtime' ]:
            if t in msg:
                msg[ t ] = timev2tov3str( msg[ t ] )

        if 'sum' in msg:
            sum_algo_map = { "a":"arbitrary", "d":"md5", "s":"sha512", 
               "n":"md5name", "0":"random", "L":"link", "R":"remove", "z":"cod" }
            sm = sum_algo_map[ msg["sum"][0] ]
            if sm in [ 'random' ] :
                sv = msg["sum"][2:]
            elif sm in [ 'cod' ] :
                sv = sum_algo_map[ msg["sum"][2:] ]
            else:
                sv = encode( decode( msg["sum"][2:], 'hex'), 'base64' ).decode('utf-8').strip()
            msg[ "integrity" ] = { "method": sm, "value": sv }
            del msg['sum']


        if 'parts' in msg:
            ( style, chunksz, block_count, remainder, current_block ) = msg['parts'].split(',')
            if style in [ 'i' , 'p' ]:
                msg['blocks'] = {}
                msg['blocks']['method'] = {'i': 'inplace', 'p': 'partitioned'}[style]
                msg['blocks']['size'] = str(chunksz)
                msg['blocks']['count'] = str(block_count)
                msg['blocks']['remainder'] = str(remainder)
                msg['blocks']['number'] = str(current_block)
            else:
                msg['size'] = chunksz
            del msg['parts']
     
        return msg
 

class V2Wrapper:

    def __init__(self, o):
        """
           Add plugins, returning True on Success.
        """
        global logger

        # FIXME, insert parent fields for v2 plugins to use here.
        self.logger=logger
        self.logger.error('v2wrapper init done')

        self.user_cache_dir=sarra.config.get_user_cache_dir()
        self.instance = o.no

        self.plugins = {}
        for ep in sarra.config.Config.entry_points:
             self.plugins[ep] = []


    def declare_option(self,option):
        logger.info('v2plugin option: %s declared' % option)

    def add(self, opname, path):


        setattr(self,opname,None)

        if path == 'None' or path == 'none' or path == 'off':
             logger.debug("Reset plugin %s to None" % opname )
             exec( 'self.' + opname + '_list = [ ]' )
             return True

        ok,script = sarra.config.config_path('plugins',path,mandatory=True,ctype='py')
        if ok:
            logger.debug("installing %s %s" % (opname, script ) )
        else:
            logger.error("installing %s %s failed: not found " % (opname, path) )
            return False

        logger.debug('installing: %s %s' % ( opname, path ) )
        try:
            with open(script) as f:
                exec(compile(f.read(), script, 'exec'))
        except:
            logger.error("sr_config/execfile 2 failed for option '%s' and plugin '%s'" % (opname, path))
            logger.debug('Exception details: ', exc_info=True)
            return False

        if getattr(self,opname) is None:
            logger.error("%s plugin %s incorrect: does not set self.%s" % (opname, path, opname ))
            return False

        if opname == 'plugin' :
            pci = self.plugin.lower()
            exec( pci + ' = ' + self.plugin + '(self)' )
            pcv = eval( 'vars('+ self.plugin +')' )
            for when in sarra.config.Config.entry_points:
                if when in pcv:
                    logger.debug("registering %s from %s" % ( when, path ) )
                    exec( 'self.' + when + '=' + pci + '.' + when )
                    eval( 'self.plugins["' + when + '"].append(' + pci + '.' + when + ')' )
        else:
            #eval( 'self.' + opname + '_list.append(self.' + opname + ')' )
            eval( 'self.plugins["' + opname +'"].append( self.' + opname + ')' )

        # following gives backward compatibility with existing plugins that don't follow new naming convention.

        return True


    def run(self,ep,m):
        """
           run plugins for a given entry point.
        """
        v2m = Message(m)

