import codecs
import os
import re
import sys

from setuptools import find_packages
from distutils.core import setup

import sarracenia

here = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    return codecs.open(os.path.join(here, *parts), 'r').read()


packages = find_packages()
print("packages = %s" % packages)

setup(
    name='metpx-sr3',
    python_requires='>3.4',
    version=sarracenia.__version__,
    description='Subscribe, Acquire, and Re-Advertise products.',
    long_description=(read('README.rst') + '\n\n' + read('CHANGES.rst') +
                      '\n\n' + read('AUTHORS.rst')),
    url='https://github.com/MetPX/sarracenia',
    license='GPLv2',
    author='Shared Services Canada, Supercomputing, Data Interchange',
    author_email='Peter.Silva@canada.ca',
    packages=find_packages(),
    package_data={'sarracenia': ['examples/*/*']},
    entry_points={
        "console_scripts": [
            "sr3=sarracenia.sr:main",
            "sr3_post=sarracenia.sr_post:main",
            #"sr3_poll=sarracenia.sr_flow:main",
            #"sr3_report=sarracenia.sr_flow:main",
            #"sr3_watch=sarracenia.sr_flow:main",
            #"sr3_winnow=sarracenia.sr_flow:main",
            #"sr3_sarra=sarracenia.sr_flow:main",
            #"sr3_shovel=sarracenia.sr_flow:main",
            #"sr3_sender=sarracenia.sr_flow:main",
            #"sr3_subscribe=sarracenia.sr_flow:main",
            #"sr3_log2save=sarracenia.sr_log2save:main",
            "sr3_tailf=sarracenia.sr_tailf:main"
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
        "amqp", "appdirs", "dateparser", "watchdog", "netifaces", "humanize", "jsonpickle",
        "paho-mqtt>=1.5.1", "paramiko", "psutil>=5.3.0"
    ])
