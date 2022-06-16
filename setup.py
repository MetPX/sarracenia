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
    long_description=(read('README.rst')),
    url='https://github.com/MetPX/sarracenia',
    license='GPLv2',
    author='Shared Services Canada, Supercomputing, Data Interchange',
    author_email='Peter.Silva@canada.ca',
    packages=find_packages() ,
    package_data={ 'sarra': [ 'examples/*/*' ] },
    entry_points={
        "console_scripts":[
              "sr_audit=sarra.sr_audit:main",
              "sr=sarra.sr:main",
              "sr1=sarra.sr1:main",
              "sr_report=sarra.sr_report:main",
              "sr_poll=sarra.sr_poll:main",
              "sr_post=sarra.sr_post:main",
              "sr_watch=sarra.sr_watch:main",
              "sr_winnow=sarra.sr_winnow:main",
              "sr_sarra=sarra.sr_sarra:main",
              "sr_shovel=sarra.sr_shovel:main",
              "sr_sender=sarra.sr_sender:main",
              "sr_subscribe=sarra.sr_subscribe:main",
              "sr_log2save=sarra.sr_log2save:main",
              "sr_tailf=sarra.sr_tailf:main"
              ]
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Communications :: File Sharing',
        'Topic :: System :: Logging',
    ],
    install_requires=[ 
    "amqp",
    "appdirs",
    "watchdog", 
    "netifaces", 
    "humanize",
    "psutil",
    "dateparser"]

)
