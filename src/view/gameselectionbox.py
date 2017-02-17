# Bulletproof Arma Launcher
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

from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from view.themedpopup import ThemedPopup

default_title = '''Select your server:'''


class GameSelectionBox(ThemedPopup):
    def close_and_run(self, func, *args):
        """There is probably a simpler way of doing this but oh well..."""
        self.dismiss()
        func(*args)

    def __init__(self, on_selection, servers=[], title=default_title,
                 markup=False, on_dismiss=None, default_teamspeak=None):
        bl = BoxLayout(orientation='vertical', padding=(0, 20))

        buttons_count = 2  # Run arma and cancel

        for server in servers:
            buttons_count += 1
            button = Button(text=server.name, size_hint_x=0.8, pos_hint={'center_x': 0.5})
            button.bind(on_release=lambda x, server=server, on_selection=on_selection: self.close_and_run(on_selection, server.name))
            bl.add_widget(button)

        bl.add_widget(Widget())  # Spacer

        button = Button(text='No server, just run Arma 3', size_hint_x=0.8, pos_hint={'center_x': 0.5})
        button.bind(on_release=lambda x, on_selection=on_selection: self.close_and_run(on_selection, None))
        bl.add_widget(button)

        bl.add_widget(Widget())  # Spacer

        button = Button(text='Cancel', size_hint_x=0.5, pos_hint={'center_x': 0.5})
        button.bind(on_release=self.dismiss)
        bl.add_widget(button)

        popup_height = 140 + (26 * buttons_count)

        super(GameSelectionBox, self).__init__(
            title=default_title, content=bl, size_hint=(None, None), size=(300, popup_height))

        # Bind an optional handler when the user closes the message
        if on_dismiss:
            self.bind(on_dismiss=on_dismiss)
