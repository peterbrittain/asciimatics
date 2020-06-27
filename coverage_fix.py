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
import sqlite3

# Simple hack to fix up the path names so that the appveyor-artifacts
# mangling finds and fixes up paths as expected in code coverage results.
#
# This script does a search and replace on the whole file.
from os.path import isfile

REGEX_MANGLE = re.compile(r'C:\\projects\\.*?')

for name in sys.argv[1:]:
    if isfile(name):
        try:
            # Latest version of coverage uses sqlite3 for the coverage files.
            conn = sqlite3.connect(name)

            # Updated logic from appveyor-artifacts while waiting for formal
            # patch.
            print("Processing {}".format(name))
            for id, windows_file in conn.execute("SELECT id, path from file"):
                print('  Found: {}'.format(windows_file))
                windows_path = REGEX_MANGLE.search(windows_file)
                if windows_path:
                    unix_relative_path = windows_file.replace('\\', '/').split('/', 3)[-1]
                    unix_absolute_path = os.path.abspath(unix_relative_path)
                    if not os.path.isfile(unix_absolute_path):
                        print('No such file: {}'.format(unix_absolute_path))
                        sys.exit(1)
                    conn.execute("UPDATE file SET path='{}' WHERE id={}".format(unix_absolute_path, id))
                    print('  Converted to: {}'.format(unix_absolute_path))
            conn.commit()
        finally:
            conn.close()
    else:
        print("Skipping directory {}".format(name))
