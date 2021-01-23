#!/usr/bin/env python3

# This file is part of sarracenia.
# The sarracenia suite is Free and is proudly provided by the Government of Canada
# Copyright (C) Her Majesty The Queen in Right of Canada, Environment Canada, 2020
#

import sys
import os
import os.path
import inspect
from sarracenia.config import Config

# this stub is included in v3 to allow v02 users to continue to use the familiar
# invocation of individual components, however, all set up is now done through
# central sr.py script.

sys.argv[-1] = os.path.basename(sys.argv[0]).replace('sr_', '').replace(
    '.py', '') + os.sep + sys.argv[-1]
args = [
    sys.executable,
    os.path.dirname(inspect.getfile(Config)) + os.sep + 'sr.py'
]
args.extend(sys.argv[1:])

os.execvp(sys.executable, args)
