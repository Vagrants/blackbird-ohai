#!/usr/bin/env python
# -*- codig: utf-8 -*-

import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='blackbird-ohai',
    version='0.1.0',
    description=(
        'get ohai information.'
    ),
    long_description=read('PROJECT.txt'),
    classifiers=[
      'Development Status :: 4 - Beta',
      'Programming Language :: Python :: 2',
      'Programming Language :: Python :: 2.6',
    ],
    author='makocchi',
    author_email='makocchi@gmail.com',
    url='https://github.com/Vagrants/blackbird-ohai',
    data_files=[
        ('/opt/blackbird/plugins', ['ohai.py']),
        ('/etc/blackbird/conf.d', ['ohai.cfg'])
    ],
    test_suite='tests',
)
