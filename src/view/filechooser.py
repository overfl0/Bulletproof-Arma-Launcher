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

import os

from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.logger import Logger


class FileChooser(Popup):
    """docstring for FileChooser"""
    def __init__(self, **kwargs):

        self.ok_pressed = False

        bl = BoxLayout(orientation='vertical', spacing=10)
        self.bound_textfield = kwargs.get('bound_textfield', None)

        fc = FileChooserListView(**kwargs)
        fc.filters = [self.file_filter]
        ti = TextInput(id='pathinput', multiline=False, height=30,
                       size_hint_y=None)

        # buttons
        buttons = BoxLayout(orientation='horizontal', height=30,
                            size_hint_y=None)

        ok_button = Button(text='Ok')
        ok_button.bind(on_release=self.on_ok_button_release)
        cancel_button = Button(text='Cancel')
        cancel_button.bind(on_release=self.on_cancel_button_release)
        buttons.add_widget(ok_button)
        buttons.add_widget(cancel_button)

        fc.bind(selection=self.on_file_chooser_selection)

        bl.add_widget(fc)
        bl.add_widget(ti)
        bl.add_widget(buttons)

        self.textinput = ti
        self.textinput.text = kwargs.get('path', '')

        super(FileChooser, self).__init__(title='Choose directory',
            content=bl, size_hint=(None, None), size=(600, 400))

        # define event for which gets fired if the user hits okay
        self.register_event_type('on_ok')

    def on_ok(*args):
        Logger.info('FileChooser: dispatched: ' + str(args))
        pass

    def on_file_chooser_selection(self, fc, value):
        text = ''
        if len(value) > 0:
            text = value[0]
        self.textinput.text = text

    def file_filter(self, folder, path):
        Logger.info('filtering path: ' + path)

        # we have to correspond to kivys very weird behaivor of evaluating
        # filters. Check in kivy is: if list(<returnvalue of this function>)
        if os.path.isdir(path):
            return [True]
        else:
            return []

    def on_ok_button_release(self, btn):
        self.dispatch('on_ok', self.textinput.text)
        self.dismiss()

    def on_cancel_button_release(self, btn):
        self.dismiss()
