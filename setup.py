"""
A setuptools based setup module for asciimatics.

Based on the sample Python packages at:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from codecs import open as file_open
from os import path
from setuptools import setup, find_packages


# Get the long description from the relevant file and strip any pre-amble (i.e. badges) from it.
here = path.abspath(path.dirname(__file__))
with file_open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read().split("\n")
while long_description[0] not in ("ASCIIMATICS", "ASCIIMATICS\r"):
    long_description = long_description[1:]
long_description = "\n".join(long_description)

setup(
    name='asciimatics',
    use_scm_version={
        "write_to": "asciimatics/version.py",
        "local_scheme": "no-local-version"
    },
    description='A cross-platform package to replace curses (mouse/keyboard '
                'input & text colours/positioning) and create ASCII '
                'animations',
    long_description=long_description,
    url='https://github.com/peterbrittain/asciimatics',
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
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
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
        'wcwidth',
    ],
    extras_require={
        ':sys_platform == "win32"': ['pywin32'],
    },
    setup_requires=['setuptools_scm'],
    python_requires=">= 3.8",
)
