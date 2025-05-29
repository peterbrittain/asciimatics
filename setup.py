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
    long_description=long_description,
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
)
