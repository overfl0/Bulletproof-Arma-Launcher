# Tactical Battlefield Installer/Updater/Launcher
# Copyright (C) 2016 TacBF Installer Team.
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

from mock import patch, Mock, MagicMock
from kivy.clock import Clock

from nose.plugins.attrib import attr
from utils.data.model import Model

class ExampleModel(Model):

    fields = [
        {'name': 'use_exception_popup', 'defaultValue': False},
        {'name': 'self_update', 'defaultValue': False},
        {'name': 'launcher_basedir'},
        {'name': 'launcher_moddir'},
        {'name': 'mod_data_cache', 'defaultValue': None}
    ]

    def __init__(self):
        super(ExampleModel, self).__init__()

class ModelTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_models_set_method_is_returning_model_itself(self):
        e = ExampleModel()
        e = e.set('self_update', True)
        self.assertIsInstance(e, ExampleModel)

    def test_model_should_fire_change_event(self):
        e = ExampleModel()
        m = MagicMock()
        e.bind(on_change=m)
        e = e.set('self_update', True)
        self.assertIsInstance(e, ExampleModel)
        Clock.tick()
        Clock.tick()
        Clock.tick()
        m.assert_called_once_with(e, 'self_update', False, True)
