#!/usr/bin/env python

from subprocess import run
from sys import argv
from sys import executable


def dust(files=[]):
    '''
    Runs a flake8 lint wrapping pyCodeStyle (used to be pep8)
    '''
    # Confirm flake8 Module is installed
    try:
        __import__('importlib').import_module('flake8')
    except ImportError:
        print("\033[1;31mFlake8 module not found, please run \033[0;30;42mpip install flake8\033[0m")
        exit(1)

    returnCode = run([executable, "-m", "flake8",
                      "--format=\033[1;31m %(path)s:%(row)d|%(col)d\033[0m:[%(code)s] %(text)s"
                      ] + files).returncode

    if (returnCode > 0):
        print("\033[0;30;41m Please Correct the above pep8 errors prior to commiting. \033[0m")

    exit(returnCode)


# If someone attempts to run it as a script, dust the lint.
if __name__ == '__main__':
    dust(argv[1:])
