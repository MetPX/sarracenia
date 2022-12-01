# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2008-2020
#
# Sarracenia repository: https://github.com/MetPX/sarracenia
# Documentation: https://github.com/MetPX/sarracenia
#
"""
  plugins that use primarily the after_work entry point, normally 
  executed after the file transfer (either send or get) has completed.

  usually such plugins will contain a loop:

  for msg in worklist.ok
      do_something.

  to operate on all the files transferrred or processed successfully.

"""
pass
