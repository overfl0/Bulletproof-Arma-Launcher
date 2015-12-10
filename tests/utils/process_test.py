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
import sys
import json

from mock import patch, Mock
from kivy.clock import Clock

from nose.plugins.attrib import attr
from utils.process import Para

def worker_func(con, arg1, arg2):
    con.resolve('something')

def termination_func(con):
    """this function is run in another process"""
    con.progress({'msg': 'test_func_has_started'})

    termination_challanged = False
    while termination_challanged == False:
        time.sleep(1)
        termination_challanged = con.wants_termination()

    con.resolve('terminating')


class ParaTest(unittest.TestCase):

    def setUp(self):
        # To fix the Windows forking system it's necessary to point __main__ to
        # the module we want to execute in the forked process
        self.old_main =                     sys.modules["__main__"]
        self.old_main_file =                sys.modules["__main__"].__file__
        sys.modules["__main__"] =           sys.modules["tests.utils.process_test"]
        sys.modules["__main__"].__file__ =  sys.modules["tests.utils.process_test"].__file__

    def tearDown(self):
        sys.modules["__main__"] =           self.old_main
        sys.modules["__main__"].__file__ =  self.old_main_file

    def test_para_should_resolve(self):
        # do your testing here
        res_handler = Mock()

        p = Para(worker_func, (1, 2), 'actionname')
        p.then(res_handler, None, None)
        p.run()
        self.assertIsNotNone(p)

        for i in range(1,120):
            Clock.tick()

        res_handler.assert_called_once_with('something')

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

    def test_para_termination(self):
        """test if a childprocess can react on termination flag of para"""
        res_handler = Mock()

        # Build a para. Register termination_test_func which has to be defined
        # at module scope because of pickling. This function could represent
        # the libtorrent side. So see above
        para = Para(termination_func, (), 'testaction')

        # register resolve handler. For reasons it has to be defined on the
        # module namespace.
        para.then(res_handler, None, None)
        para.run()

        # a check loop simulating the parent process waiting for paras
        # to resolve or reject
        count = 0
        while not para.state == 'resolved':
            time.sleep(0.5)
            Clock.tick()
            count += 1
            # send termination after 2 seconds
            if count == 4:
                para.send_termation_msg()

        res_handler.assert_called_once_with('terminating')
