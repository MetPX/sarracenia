import codecs
import itertools
import os
import re
import sys

from setuptools import find_packages
from distutils.core import setup

#import sarracenia

here = os.path.abspath(os.path.dirname(__file__))


def latest_changelog() -> str:
    
    lines=[]
    started=False
    with open('debian/changelog','r') as clf:
       for l in clf.readlines():
          if len(l) < 2: continue
          if l[2] == '*' :
             lines.append(l)  
          elif l[2] == '-': break
    return '\nChanges:\n' + '\n'.join(lines)

def read(*parts):
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    return codecs.open(os.path.join(here, *parts), 'r').read()

metadata = {}
with open(os.path.join(here, "sarracenia", "_version.py"), "r") as f:
    exec(f.read(), metadata)

packages = find_packages()
print("packages = %s" % packages)

features = {
       'amqp' : [ "amqp" ],
       'filetypes': [ "python-magic" ], 
       'ftppoll' : ['dateparser' ],
       'mqtt': [ 'paho.mqtt>=1.5.1' ],
       'vip': [ 'netifaces' ],
       'redis': [ 'redis' ]
    } 



features['all'] = list(itertools.chain.from_iterable(features.values()))

setup(
    name='metpx-sr3',
    python_requires='>=3.6',
    version=metadata["__version__"],
    description='Subscribe, Acquire, and Re-Advertise products.',
    long_description_content_type='text/x-rst',
    long_description=(read('README.rst')+latest_changelog()), 
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
            "sr3_rotateLogsManually=sarracenia.sr_rotateLogsManually:main", 
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
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Intended Audience :: System Administrators',
        'Natural Language :: English',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Communications :: File Sharing',
        'Topic :: System :: Logging',
    ],
    install_requires=[
        "appdirs", "humanfriendly", "humanize", "jsonpickle", "psutil>=5.3.0", 
        "paramiko", "watchdog",
        'xattr ; sys_platform!="win32"', 'python-magic; sys_platform!="win32"',
        'python-magic-bin; sys_platform=="win32"'
    ],
    # when building on HPC redhat, python OS packages don't exist. 
    # remove the last three lines of install_requires above, aka: 
    # paramiko, watchdog, xattr, python-magic before you do:
    # 
    #    python3 setup.py bdist_rpm

    extras_require = features
    )




