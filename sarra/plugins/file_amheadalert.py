#!/usr/bin/python3

"""
  on_file handler to process as per amheadalert

  usage:
 
  file_amheadalertrc /path/to/amheadalert/config

  on_file file_amheadalert

  syntax of amheadalertrc file:  

  >                     Append? not sure... 
                        it if is just rename then that implementation is simpler and in comments.

  | cmd                 pipe the file received to the command.

  header TTAAii CCCC    header to apply 

"""

import os,os.path,stat,time

class File_Amheadalert: 

    def __init__(self,parent):

        parent.declare_option('file_amheadalertrc')

        if not hasattr(parent,'file_amheadalertrc'):
            parent.logger.error("file_amheadalertrc path needed.")
            return

        parent.logger.info("file_amheadalertrc is: %s" % parent.file_amheadalertrc[0] )
        if not os.path.exists(parent.file_amheadalertrc[0]):
            parent.logger.error("file_amheadalertrc path needed.")
            return

        self.ahl_processing={}
        with open(parent.file_amheadalertrc[0],'r') as f:
            for fl in f.readlines() :
                parent.logger.debug('line is: %s, %s, %s' % (fl[0], fl[0:7], fl) )
                if fl[0] in [ '>', '|']:
                    parent.logger.debug( 'captured' )
                    processing_line=fl.strip()
                elif fl[0:7] == 'header ':
                    fll = fl[7:].strip().lower()
                    parent.logger.debug( 'ahl_processing[ %s ] = %s' % (fll, processing_line ))
                    self.ahl_processing[ fll ] = processing_line 
                else:
                    parent.logger.debug( 'discarded' )

        parent.logger.info("file_amhdalrt initialized")
          
    def on_file(self,parent):
        import os.path
        import shutil
        import subprocess

        fn=os.path.normpath( parent.msg.new_dir + '/' + parent.msg.new_file )
        ttaaii=parent.msg.new_file[0:6].lower()
        cccc=parent.msg.new_file[7:11].lower()
        parent.logger.info("header= %s %s" % (ttaaii,cccc) )
        key = ttaaii + ' ' + cccc
        if key in self.ahl_processing:
            p=self.ahl_processing[key]
            if p[0] == '>':
               parent.logger.info('catenating: %s to %s ' % (fn, p[2:] ))
               # does > mean move/rename? or append? dunno amheadalert.
               # rename version:
               shutil.move( fn ,p[2:] )             
               # append version:
               #with open(p[2:],'a+') as d:
               #   with open(fn,'r') as s:
               #       d.write(s.read()) 
            elif p[0] == '|':
               cmd= "cat %s %s" % (fn,p)
               parent.logger.info('piping: %s ' % (cmd ))
               parent.logger.info( subprocess.getoutput( cmd ) )
             
        return True


file_amheadalert = File_Amheadalert(self)

self.on_file = file_amheadalert.on_file


