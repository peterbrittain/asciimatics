"""
A setuptools based setup module for asciimatics.

Based on the sample Python packages at:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages
from codecs import open
from os import path
import sys

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='asciimatics',
    use_scm_version={"write_to": "asciimatics/version.py"},
    description='A cross-platform package to replace curses (mouse/keyboard '
                'input & text colours/positioning) and create ASCII '
                'animations',
    long_description=long_description,
    url='https://github.com/peterbrittain/asciimatics.git',
    author='Peter Brittain',
    author_email='peter.brittain.os@gmail.com',
    license='Apache 2.0',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Environment :: Console :: Curses',
        'Intended Audience :: Developers',
        'Topic :: Text Processing :: General',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: Terminals',
    ],
    keywords='ascii ansi art credits titles animation curses '
             'ncurses windows xterm mouse keyboard terminal tty '
             'color colour crossplatform console',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=[
        'pyfiglet >= 0.7.2',
        'Pillow >= 2.7.0',
        'future',
    ] + (['pypiwin32'] if sys.platform == 'win32' else []),
    setup_requires=['setuptools_scm'],
    tests_require=[
        'mock',
        'nose',
    ],
    test_suite='nose.collector',
)
