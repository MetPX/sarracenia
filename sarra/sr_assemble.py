#!/usr/bin/env python3
#
# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2015
#
# Questions or bugs report: dps-client@ec.gc.ca
# sarracenia repository: git://git.code.sf.net/p/metpx/git
# Documentation: http://metpx.sourceforge.net/#SarraDocumentation
#
# sr_assemble.py : python3 program that gets files (partitions) and 
#                    assembles them into one big file
#
#
# Code contributed by:
#  Wahaj Taseer - Shared Services Canada
#  Last Changed : July 2018
#
########################################################################
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful, 
#  but WITHOUT ANY WARRANTY; without even the implied warranty of 
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307  USA
#
#============================================================
# usage example
#
# sr_assemble [/path/to/]file* 
#
#============================================================

#


try :    
  from sr_instances import *

except : 
  from sarra.sr_instances import *



class sr_assemble(sr_instances):
  

  # ===============
  # __do_assemble__
  # ===============
  def __do_assemble__(self, files):
    logger = self.logger


    num_files = len(files)

    # Making sure there is more than 1 file
    if num_files <= 1:
      logger.warning('Nothing to assemble...')
      return

    # Check for data gaps?
    try:
      file_info = files[0].rsplit('.', 6)
      
      file_name = file_info[0]
      file_size = int(file_info[1])
      file_partitions = int(file_info[2])
      file_remainder = int(file_info[3])
      file_index = 0
      file_sumflag = file_info[5]
      file_suffix = file_info[6]

      
    except Exception as e:
      logger.error("Could not parse file name, are these the right files?")
      raise e


    # Make sure correct number of partitions are present
    if num_files != file_partitions:
      logger.info('files given: %s, Need exactly %s files. Something\'s not right...' % (num_files, file_partitions) ) 
      return


    # Iterate through list of files 
    # joining each one into a new file called file_name.assembled
    i = 0 

    f_curr = file_name+'.assembled'

    with open(f_curr, 'ab') as fo_curr: # Open file for appending in binary
      logger.info( "File: %s is open for writing" % fo_curr.name)
    
      # Loop through partitions
      while i < file_partitions:
        f_next = file_name+'.'+str(file_size)+'.'+str(file_partitions)+'.'+str(file_remainder)+'.'+str(i)+'.'+file_sumflag+'.'+file_suffix
        
        with open(f_next, 'rb') as fo_next: # Open file for reading in binary
          
          # Loop through each partition in 4 KiB piece
          piece = fo_next.read(4096)
          while piece:
            fo_curr.write(piece)
            piece = fo_next.read(4096)

        fo_next.closed

        logger.info( "File: %s has been written to %s, and is being removed" % (fo_next.name, fo_curr.name))
        
        try:
          os.remove(fo_next.name)
        except Exception as e:
          logger.error("Failed to remove %s", fo_next.name)          

        i+=1  

    fo_curr.closed
    

# ===================================
# MAIN
# ===================================

def main():

  assembler = sr_assemble()
  assembler.__do_assemble__(sys.argv[1:])

  os._exit(0)

# =========================================
# direct invocation
# =========================================

if __name__=="__main__":
  main()
