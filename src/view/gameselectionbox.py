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

from __future__ import unicode_literals

import sys

from kivy.logger import Logger
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from utils import browser

default_title = """Connect to server:"""


def open_hyperlink(obj, ref):
    browser.open_hyperlink(ref)


def connect_to_server(server):
    Logger.info('GameSelectionBox: User selected server: {}'.format(server['uri']))


class GameSelectionBox(Popup):
    def __init__(self, servers=[], title=default_title, markup=False, on_dismiss=None):
        bl = BoxLayout(orientation='vertical')

        '''la = Label(text=text, size_hint_y=0.8, markup=markup)
        la.bind(on_ref_press=open_hyperlink)
        bl.add_widget(la)'''

        button = Button(text="Run Arma 3") #, size_hint_y=0.2)
        button.bind(on_release=self.dismiss)
        bl.add_widget(button)

        bl.add_widget(Widget())  # Spacer

        for server in servers:
            button = Button(text=server['name'], size_hint_x=0.8, pos_hint={'center_x': 0.5}) #, size_hint_y=0.2)
            button.bind(on_release=lambda x, server=server: connect_to_server(server))
            bl.add_widget(button)

        bl.add_widget(Widget())  # Spacer

        button = Button(text="Cancel")#, size_hint_y=0.2)
        button.bind(on_release=self.dismiss)
        bl.add_widget(button)

        super(GameSelectionBox, self).__init__(
            title=title, content=bl, size_hint=(None, None), size=(200, 300))

        # Bind an optional handler when the user closes the message
        if on_dismiss:
            self.bind(on_dismiss=on_dismiss)
