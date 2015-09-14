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
    url='http://metpx.sf.net',
    license='LGPL',
    author='Dads',
    author_email='peter_silva@sourceforge.net',
    packages=find_packages(),
    entry_points={
        "console_scripts":[
              "dd_post=sara.dd_post:main",
              "dd_sara=sara.dd_sara:main",
              "dd_sender=sara.dd_sender:main",
              "dd_watch=sara.dd_watch:main",
              "dd_subscribe=sara.dd_subscribe:main",
              "dd_log2source=sara.dd_log2source:main"
              ]
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
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
