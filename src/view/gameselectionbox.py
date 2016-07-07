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

from kivy.logger import Logger
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from utils.devmode import devmode

default_title = """Connect to server:"""


def sanitize_server_list(servers):
    """Filter out only the servers that contain a 'name', 'ip' and 'port' fields."""

    checked_servers = servers[:]
    extra_server_string = devmode.get_extra_server()

    if extra_server_string:
        extra_server = {k: v for (k, v) in zip(('name', 'ip', 'port'), extra_server_string.split(':'))}
        checked_servers.insert(0, extra_server)

    ret_servers = filter(lambda x: all((x.get('name'), x.get('ip'), x.get('port'))), checked_servers)

    return ret_servers


def connect_to_server(server):
    name = server.get('name', '<no_name>')
    IP = server.get('ip', '127.0.0.1')
    port = server.get('port', '0')
    Logger.info('GameSelectionBox: User selected server: {} ({}:{})'.format(name, IP, port))


class GameSelectionBox(Popup):
    def __init__(self, servers=[], title=default_title, markup=False, on_dismiss=None):
        bl = BoxLayout(orientation='vertical')

        button = Button(text="Run Arma 3") #, size_hint_y=0.2)
        button.bind(on_release=self.dismiss)
        bl.add_widget(button)

        bl.add_widget(Widget())  # Spacer

        for server in sanitize_server_list(servers):
            button = Button(text=server.get('name', '<no name>'), size_hint_x=0.8, pos_hint={'center_x': 0.5}) #, size_hint_y=0.2)
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
