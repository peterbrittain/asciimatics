# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from datetime import datetime
import time
import unittest
from asciimatics.utilities import readable_mem, readable_timestamp


class TestWidgets(unittest.TestCase):

    def test_readable_mem(self):
        """
        Check readable_mem works as expected.
        """
        # Check formatting works as expected.
        self.assertEquals("9999", readable_mem(9999))
        self.assertEquals("10K", readable_mem(10240))
        self.assertEquals("1024K", readable_mem(1024*1024))
        self.assertEquals("10M", readable_mem(1024*1024*10))
        self.assertEquals("10G", readable_mem(1024*1024*1024*10))
        self.assertEquals("10T", readable_mem(1024*1024*1024*1024*10))
        self.assertEquals("10P", readable_mem(1024*1024*1024*1024*1024*10))

    def test_readable_timestamp(self):
        """
        Check readable_timestamp works as expected.
        """
        # Check formatting works as expected.
        self.assertEquals("12:01:02AM", readable_timestamp(
            time.mktime(datetime.now().replace(hour=0, minute=1, second=2).timetuple())))
        self.assertEquals("1999-01-02", readable_timestamp(
            time.mktime(datetime.now().replace(year=1999, month=1, day=2).timetuple())))
