import codecs
import os
import re
import sys

from setuptools import find_packages
from distutils.core import setup

import sarra

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    return codecs.open(os.path.join(here, *parts), 'r').read()

packages=find_packages()
print("packages = %s" % packages)

setup(
    name='metpx-sarracenia',
    version=sarra.__version__,
    description='Subscribe, Acquire, and Re-Advertise products.',
    long_description=(read('README.rst') + '\n\n' +
                      read('CHANGES.txt') + '\n\n' +
                      read('AUTHORS.txt')),
    url='http://metpx.sourceforge.net/',
    license='GPLv2',
    author='Shared Services Canada, Supercomputing, Data Interchange',
    author_email='Peter.Silva@canada.ca',
    packages=find_packages(),
    entry_points={
        "console_scripts":[
              "sr_audit=sarra.sr_audit:main",
              "sr=sarra.sr:main",
              "sr_2xreport=sarra.sr_2xreport:main",
              "sr_report=sarra.sr_report:main",
              "sr_report2clusters=sarra.sr_report2clusters:main",
              "sr_report2source=sarra.sr_report2source:main",
              "sr_poll=sarra.sr_poll:main",
              "sr_post=sarra.sr_post:main",
              "sr_watch=sarra.sr_watch:main",
              "sr_winnow=sarra.sr_winnow:main",
              "sr_sarra=sarra.sr_sarra:main",
              "sr_shovel=sarra.sr_shovel:main",
              "sr_sender=sarra.sr_sender:main",
              "sr_subscribe=sarra.sr_subscribe:main",
              ]
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Communications :: File Sharing',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Logging',
    ],
    install_requires=[ 
    "amqplib", 
    "appdirs",
    "watchdog", 
    "netifaces", 
    "paramiko",
    "humanize",
    "psutil" ],
)
