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
import os

from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from view.filechooser import FileChooser
from view.errorpopup import ErrorPopup


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
        settings_active = self.settings.get(value + '_enabled')
        self.ids.textinput.text = settings_value
        self.ids.checkbox.active = bool(settings_active)

    def save_settings(self, instance, value):
        if not self.settings_name:
            return

        self.settings.set(self.settings_name + '_enabled', self.ids.checkbox.active)
        self.settings.set(self.settings_name, self.ids.textinput.text)


class StringLabel(BoxLayout):

    settings_name = StringProperty(None)
    field_value = StringProperty(None)

    def __init__(self, entries=None, on_manual_path=None, **kwargs):
        self.settings = kivy.app.App.get_running_app().settings
        super(StringLabel, self).__init__(**kwargs)

        self.bind(settings_name=self.set_settings_name)

    def set_settings_name(self, instance, value):
        if not value:
            return

        settings_value = self.settings.get(value)
        self.ids.textinput.text = settings_value

    def save_settings(self, instance, value):
        if not self.settings_name:
            return

        self.settings.set(self.settings_name, self.ids.textinput.text)
        self.field_value = self.ids.textinput.text


class CheckDropdownLabel(BoxLayout):

    settings_name = StringProperty(None)

    def __init__(self, entries=None, on_manual_path=None, **kwargs):
        self.settings = kivy.app.App.get_running_app().settings
        super(CheckDropdownLabel, self).__init__(**kwargs)

        self.bind(settings_name=self.set_settings_name)

    def set_settings_name(self, instance, value):
        if not value:
            return

        settings_value = self.settings.get(value)
        settings_active = self.settings.get(value + '_enabled')
        self.ids.dropdown.default = settings_value
        # self.ids.dropdown.text = settings_value
        self.ids.checkbox.active = bool(settings_active)

    def save_settings(self, instance, value):
        if not self.settings_name:
            return

        self.settings.set(self.settings_name + '_enabled', self.ids.checkbox.active)
        self.settings.set(self.settings_name, self.ids.dropdown.text)


class CheckFileLabel(BoxLayout):

    settings_name = StringProperty(None)

    def __init__(self, entries=None, on_manual_path=None, **kwargs):
        self.settings = kivy.app.App.get_running_app().settings
        super(CheckFileLabel, self).__init__(**kwargs)

        self.bind(settings_name=self.set_settings_name)

    def set_settings_name(self, instance, value):
        if not value:
            return

        settings_value = self.settings.get(value)
        settings_active = self.settings.get(value + '_enabled')
        self.ids.textinput.text = settings_value
        self.ids.checkbox.active = bool(settings_active)

    def save_settings(self, *args, **kwargs):
        if not self.settings_name:
            return

        self.settings.set(self.settings_name + '_enabled', self.ids.checkbox.active)
        self.settings.set(self.settings_name, self.ids.textinput.text)

    def path_chosen_cb(self, path):
        if not os.path.isfile(path):
            return 'This is not a file: {}'.format(path)

        self.ids.textinput.text = path
        self.save_settings(None, None)

    def choose_path(self):
        self.p = FileChooser(self.ids.textinput.text,
                             on_success=self.path_chosen_cb,
                             select_dir=False,
                             filetypes=[('SQM files', '*.sqm'), ('All files', '*')])


class Devmode_options(GridLayout):
    def __init__(self, mod_manager, *args, **kwargs):
        super(Devmode_options, self).__init__(*args, **kwargs)
        self.mod_manager = mod_manager

    def show_torrents(self, option):
        options = ('base_server', 'server', 'base', 'all')
        if option not in options:
            raise Exception('Unsupported torrent option')

        try:
            if option == 'base_server':
                mods = self.mod_manager.get_mods(include_base=True, include_server=True, include_all_servers=False)

            elif option == 'server':
                mods = self.mod_manager.get_mods(include_base=False, include_server=True, include_all_servers=False)

            elif option == 'base':
                mods = self.mod_manager.get_mods(include_base=True, include_server=False, include_all_servers=False)

            elif option == 'all':
                mods = self.mod_manager.get_mods(include_base=True, include_server=True, include_all_servers=True)

        except KeyError:
            ErrorPopup(message='The server data is probably still being fetched. Wait a few seconds and retry.').chain_open()
            return

        details = '\n'.join(mod.torrent_url for mod in mods)
        title = 'Torrents exporter'

        if mods:
            message = 'The torrent URLs have been copied to your clipboard. Press Ctrl+V to paste them.'
        else:
            message = 'No mods meeting the criteria were found.'


        ErrorPopup(details=details, message=message, title=title, size=(900, 400)).chain_open()


Builder.load_file('kv/simplewidgets.kv')
