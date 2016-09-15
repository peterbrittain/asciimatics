# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
import re
import sys

# Simple hack to fix up the path names so that the appveyor-artifacts
# mangling finds and fixes up paths as expected in code coverage results.
#
# This script does a search and replace on the whole file.
from os.path import isfile

for name in sys.argv[1:]:
    if isfile(name):
        try:
            with open(name) as file:
                coverage = "".join(file.readlines())

            print("Processing {}".format(name))
            coverage = re.sub(r'\\\\Projects', r'\\\\projects', coverage)

            with open(name, "w") as file:
                file.writelines(coverage)
        except UnicodeDecodeError:
            print("Skipping binary file {}".format(name))
    else:
        print("Skipping directory {}".format(name))