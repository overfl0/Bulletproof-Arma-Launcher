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


class FileChooser(Popup):
    """docstring for FileChooser"""
    def __init__(self, **kwargs):

        self.browser = FileBrowser(**kwargs)

        self.browser.bind(on_success=self._fbrowser_success,
                          on_canceled=self._fbrowser_canceled)

        super(FileChooser, self).__init__(title='Choose directory',
                                          content=self.browser,
                                          size_hint=(None, None),
                                          size=(900, 600))

        # define event for which gets fired if the user hits okay
        self.register_event_type(b'on_ok')

        Clock.schedule_once(self._on_next_frame, 0)

    def _on_next_frame(self, dt):
        file_list = self.browser.ids.list_view
        file_list.filters = [self.file_filter]

        return False

    def on_ok(*args):
        Logger.info('FileChooser: dispatched: ' + str(args))
        pass

    def _fbrowser_canceled(self, instance):
        self.dismiss()

    def _fbrowser_success(self, instance):
        pass

    def on_file_chooser_selection(self, fc, value):
        text = ''
        if len(value) > 0:
            text = value[0]
        self.textinput.text = text

    def file_filter(self, folder, path):
        # we have to correspond to kivys very weird behaivor of evaluating
        # filters. Check in kivy is: if list(<returnvalue of this function>)
        if os.path.isdir(path):
            return [True]
        else:
            return []

    def on_ok_button_release(self, btn):
        self.dispatch(b'on_ok', self.textinput.text)
        self.dismiss()

    def on_cancel_button_release(self, btn):
        self.dismiss()
