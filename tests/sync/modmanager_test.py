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
from nose.plugins.attrib import attr

from sync.modmanager import ModManager
from sync.mod import Mod
from sync.httpsyncer import HttpSyncer

class AppMock(object):
    """docstring for AppMock"""
    def __init__(self):
        super(AppMock, self).__init__()
        self.settings = None

    @classmethod
    def get_running_app(cls):
        return AppMock()

class ModManagerTest(unittest.TestCase):

    def setUp(self):
        pass

    @patch('kivy.app.App', AppMock)
    def test_modmanager_should_be_createable(self):
        m = ModManager()
        self.assertIsNotNone(m)
