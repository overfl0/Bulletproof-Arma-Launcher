# Bulletproof Arma Launcher
# Copyright (C) 2017 Lukasz Taczuk
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

from __future__ import unicode_literals

import kivy.app

from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout


class CheckLabel(BoxLayout):

    settings_name = StringProperty(None)

    def __init__(self, entries=None, on_manual_path=None, **kwargs):
        self.settings = kivy.app.App.get_running_app().settings
        super(CheckLabel, self).__init__(**kwargs)

        self.bind(settings_name=self.set_settings_name)

    def set_settings_name(self, instance, value):
        if not value:
            return

        self.ids.checkbox.active = bool(self.settings.get(value))

    def save_settings(self, instance, value):
        if not self.settings_name:
            return

        self.settings.set(self.settings_name, value)


class CheckStringLabel(BoxLayout):

    settings_name = StringProperty(None)

    def __init__(self, entries=None, on_manual_path=None, **kwargs):
        self.settings = kivy.app.App.get_running_app().settings
        super(CheckStringLabel, self).__init__(**kwargs)

        self.bind(settings_name=self.set_settings_name)

    def set_settings_name(self, instance, value):
        if not value:
            return

        settings_value = self.settings.get(value)
        self.ids.textinput.text = settings_value
        self.ids.checkbox.active = bool(settings_value)

    def save_settings(self, instance, value):
        if not self.settings_name:
            return

        if not self.ids.checkbox.active:
            self.settings.set(self.settings_name, '')
        else:
            self.settings.set(self.settings_name, self.ids.textinput.text)


Builder.load_file('kv/simplewidgets.kv')
