import codecs
import os
import re
import sys

from setuptools import setup,find_packages

here = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    return codecs.open(os.path.join(here, *parts), 'r').read()

packages=find_packages()
print("packages = %s" % packages)

setup(
    name='sara',
    version='0.0.1',
    description='Subscribe and readvertise products.',
    long_description=(read('README.rst') + '\n\n' +
                      read('CHANGES.txt') + '\n\n' +
                      read('AUTHORS.txt')),
    url='https://github.com/petersilva/metpx.git/sarracenia',
    license='LGPL',
    author='Dads',
    author_email='peter.silva@ssc-spc.gc.ca',
    packages=find_packages(),
    entry_points={
        "console_scripts":[
              "sr_post=sara.sr_post:main",
              "sr_log=sara.sr_log:main",
              "sr_sara=sara.sr_sara:main",
              "sr_sender=sara.sr_sender:main",
              "sr_watch=sara.sr_watch:main",
              "sr_subscribe=sara.sr_subscribe:main",
              "sr_log2source=sara.sr_log2source:main",
              "sr_log2clusters=sara.sr_log2clusters:main"
              ]
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
