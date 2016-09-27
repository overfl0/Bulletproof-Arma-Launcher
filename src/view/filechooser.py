# Bulletproof Arma Launcher
# Copyright (C) 2016 Sascha Ebert
# Copyright (C) 2016 Lukasz Taczuk
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

import os

from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.logger import Logger
from kivy.clock import Clock
from view.filebrowser import FileBrowser

# Until Kivy 1.9.2, you NEED to have the following patches applied;
# https://github.com/kivy/kivy/commit/b1b5da3f0dd38848302703d7c2347e22682c0649
# https://github.com/kivy/kivy/commit/e75575c2a58a71e9481628045111ddad94ed19e8

class FileChooser(Popup):
    """docstring for FileChooser"""
    def __init__(self, **kwargs):

        self.browser = FileBrowser(**kwargs)

        self.browser.bind(on_success=self._fbrowser_success,
                          on_canceled=self._fbrowser_canceled)

        super(FileChooser, self).__init__(title='Choose directory',
                                          content=self.browser,
                                          size_hint=(None, None),
                                          size=(900, 600),
                                          auto_dismiss=False)

        Clock.schedule_once(self._on_next_frame, 0)

    def _on_next_frame(self, dt):
        file_list = self.browser.ids.list_view
        file_list.filters = [self.file_filter]

        return False

    def _fbrowser_canceled(self, instance):
        self.dismiss()

    def _fbrowser_success(self, instance):
        pass

    def file_filter(self, folder, path):
        return os.path.isdir(path)
