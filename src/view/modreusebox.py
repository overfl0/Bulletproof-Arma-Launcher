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

from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from utils import browser
from view.chainedpopup import ChainedPopup

default_title = '''A similar mod has been found on the disk:'''


def open_hyperlink(obj, ref):
    browser.open_hyperlink(ref)


class ModReuseBox(ChainedPopup):
    def close_and_run(self, func, *args):
        """There is probably a simpler way of doing this but oh well..."""
        self.dismiss()
        func(*args)

    def __init__(self, on_selection, mod_name, locations=[], title=default_title,
                 markup=False, on_dismiss=None, default_teamspeak=None):
        bl = BoxLayout(orientation='vertical')

        text = '''A similar mod to {} has been found on disk.
You can ignore it and download it from the internet.
You can copy its contents.
You can use that directory.
TODO: Write some more text here.'''.format(mod_name)

        la = Label(text=text, size_hint_y=0.8, markup=markup)
        la.bind(on_ref_press=open_hyperlink)
        bl.add_widget(Widget())  # Spacer
        bl.add_widget(la)
        bl.add_widget(Widget())  # Spacer

        button = Button(text='Ignore')  # , size_hint_y=0.2)
        button.bind(on_release=lambda x, location=None, action='ignore', on_selection=on_selection: self.close_and_run(on_selection, location, action))
        bl.add_widget(button)
        bl.add_widget(Widget())  # Spacer

        for location in locations:
            la = Label(text=location, size_hint_y=0.8, markup=markup)
            la.bind(on_ref_press=open_hyperlink)
            bl.add_widget(la)

            horizontal_box = BoxLayout(orientation='horizontal')

            button = Button(text='Copy contents', size_hint_x=0.2)
            button.bind(on_release=lambda x, location=location, action='copy', on_selection=on_selection: self.close_and_run(on_selection, location, action))
            horizontal_box.add_widget(button)

            button = Button(text='Use directly', size_hint_x=0.2)
            button.bind(on_release=lambda x, location=location, action='use', on_selection=on_selection: self.close_and_run(on_selection, location, action))
            horizontal_box.add_widget(button)

            bl.add_widget(horizontal_box)

        bl.add_widget(Widget())  # Spacer

        popup_height = 300 + (50 * len(locations))

        super(ModReuseBox, self).__init__(
            title=default_title, content=bl, size_hint=(None, None), size=(600, popup_height))

        # Bind an optional handler when the user closes the message
        if on_dismiss:
            self.bind(on_dismiss=on_dismiss)
