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

from mock import patch, MagicMock
from kivy.clock import Clock

from utils.data.model import Model, ModelInterceptorError

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

    def _set_launcher_basedir(self, value):
        return value.upper()

    def _get_launcher_moddir(self, value):
        return value.upper()

    def _set_mod_data_cache(self, value):
        return ModelInterceptorError()

class ModelTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_model_should_call_interceptors(self):
        e = ExampleModel()
        e = e.set('launcher_basedir', 'something')
        self.assertEqual(e.get('launcher_basedir'), 'SOMETHING')

        e = e.set('launcher_moddir', 'somethingelse')
        self.assertEqual(e.get('launcher_moddir'), 'SOMETHINGELSE')

        e = e.set('mod_data_cache', 'somethingelse')
        self.assertEqual(e.get('mod_data_cache'), None)

    def test_models_set_method_is_returning_model_itself(self):
        e = ExampleModel()
        e = e.set('self_update', True)
        self.assertIsInstance(e, ExampleModel)
        self.assertIn('self_update', e.data)

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
