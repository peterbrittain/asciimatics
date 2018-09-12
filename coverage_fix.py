# -*- coding: utf-8 -*-
"""
Quick fix for merging code coverage reports from appveyor with travis CI results.
"""
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
import re
import sys
import os

# Simple hack to fix up the path names so that the appveyor-artifacts
# mangling finds and fixes up paths as expected in code coverage results.
#
# This script does a search and replace on the whole file.
from os.path import isfile

REGEX_MANGLE = re.compile(r'"C:\\\\projects\\\\.*?"')

for name in sys.argv[1:]:
    if isfile(name):
        try:
            with open(name) as my_file:
                coverage = my_file.read()

            # Updated logic from appveyor-artifacts while waiting for formal
            # patch.
            print("Processing {}".format(name))
            for windows_path in set(REGEX_MANGLE.findall(coverage)):
                print('  Found: {}'.format(windows_path))
                unix_relative_path = \
                    windows_path.replace(r'\\', '/').split('/', 3)[-1][:-1]
                unix_absolute_path = os.path.abspath(unix_relative_path)
                if not os.path.isfile(unix_absolute_path):
                    print('No such file: {}'.format(unix_absolute_path))
                    sys.exit(1)
                coverage = coverage.replace(
                    windows_path, '"' + unix_absolute_path + '"')

            with open(name, "w") as my_file:
                my_file.writelines(coverage)
        except UnicodeDecodeError:
            print("Skipping binary file {}".format(name))
    else:
        print("Skipping directory {}".format(name))
