# Bulletproof Arma Launcher
# Copyright (C) 2016 Sascha Ebert
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import unittest
import time
import os
import shutil
import sys
import json

from multiprocessing import Pipe
from datetime import datetime
from datetime import timedelta
from mock import patch, Mock
from kivy.clock import Clock

from nose.plugins.attrib import attr
from utils.process import Process

def worker_func(con):
    con.send('test1')
    con.send('test2')


class EventBridgeTest(unittest.TestCase):

    def setUp(self):
        # To fix the Windows forking system it's necessary to point __main__ to
        # the module we want to execute in the forked process
        self.old_main =                     sys.modules["__main__"]
        self.old_main_file =                sys.modules["__main__"].__file__
        sys.modules["__main__"] =           sys.modules["tests.utils.event_bridge_test"]
        sys.modules["__main__"].__file__ =  sys.modules["tests.utils.event_bridge_test"].__file__

    def tearDown(self):
        sys.modules["__main__"] =           self.old_main
        sys.modules["__main__"].__file__ =  self.old_main_file

    def test_connection_can_hold_more_than_one_msg(self):
        parent_conn, child_conn = Pipe()
        p = Process(target=worker_func, args=(child_conn,))
        p.start()
        # time.sleep(2)
        self.assertEqual(parent_conn.recv(), 'test1')
        self.assertEqual(parent_conn.recv(), 'test2')
        p.join()
