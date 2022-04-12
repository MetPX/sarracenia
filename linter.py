#!/usr/bin/env python

from subprocess import run
from sys import executable

# Confirm pyCodeStyle Module is installed
try:
    import pycodestyle
except ImportError:
    print("PyCodeStyle module not found,\033[1;32m please run \033[0;30;42mpip install pycodestyle\033[0m")
    exit(1)

# Run pep8 linter
# To enforce style, see ./setup.cfg
returnCode = run([executable,
                  "-m",
                  "pycodestyle",
                  "--show-source",
                  "--format=\033[1;31m %(path)s:%(row)d|%(col)d\033[0m:[%(code)s] %(text)s",
                  "."]).returncode

# Return non-zero to trigger Git pre-commit hook/GitHub Actions?
if (returnCode > 0):
    print("\033[0;30;41m Please Correct the above pep8 errors prior to commiting. \033[0m")
    exit(returnCode)
