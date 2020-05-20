
import logging
import os
import sarra.config
import time
import types

from abc import ABCMeta, abstractmethod

from sarra.sr_util import nowflt

logger = logging.getLogger( __name__ )

class v2wrapper:

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

    def build_sr_message(self,v3m):
        """
         in v3, a message is just a dictionary. in v2 it is an object.
         build from sr_message.
        """
        # FIXME: new_dir, new_file
        # FIXME: pubtime, relpath, baseurl, 
        # FIXME: sumstr, partstr, 
        # FIXME: url (result of urlparse?)
        # FIXME: headers
        # FIXME: get_elapse()
        # FIXME: set_parts()
        

    def run(self,ep,m):
        """
           run plugins for a given entry point.
        """


