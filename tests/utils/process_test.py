# Tactical Battlefield Installer/Updater/Launcher
# Copyright (C) 2015 TacBF Installer Team.
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

from mock import patch, Mock
from kivy.clock import Clock

from nose.plugins.attrib import attr
from utils.process import Para

class ProcessMock(object):
    """docstring for ProcessMock"""
    def __init__(self, target=None, args=()):
        super(ProcessMock, self).__init__()
        self.target = target
        self.args = args

    def start(self):
        self.target(*self.args)

    def join(self):
        pass

def worker_func(con, arg1, arg2):
    con.resolve('something')

class ModManagerTest(unittest.TestCase):

    def setUp(self):
        pass

    @patch('utils.process.Process', ProcessMock)
    def test_para_should_resolve(self):

        res_handler = Mock()

        p = Para(worker_func, (1, 2), 'actionname')
        p.then(res_handler, None, None)
        p.run()
        self.assertIsNotNone(p)

        for i in range(1,120):
            Clock.tick()

        res_handler.assert_called_once_with('something')

    @patch('utils.process.Process', ProcessMock)
    def test_para_should_call_res_handler_even_if_already_resolved(self):

        res_handler = Mock()

        p = Para(worker_func, (1, 2), 'actionname')
        p.run()
        self.assertIsNotNone(p)

        for i in range(1,120):
            Clock.tick()

        self.assertEqual(p.state, 'resolved')

        p.then(res_handler, None, None)
        res_handler.assert_called_once_with('something')
