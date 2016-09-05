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

import textwrap

from functools import partial
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from utils import browser
from view.chainedpopup import ChainedPopup
from view.labelb import LabelB

default_title = '''A similar mod seems to already have been downloaded'''


def open_hyperlink(obj, ref):
    browser.open_hyperlink(ref)


class ModReuseBox(ChainedPopup):
    def close_and_run(self, func, *args):
        """There is probably a simpler way of doing this but oh well..."""
        self.unbind_uid('on_dismiss', self.custom_dismiss_uid)
        self.dismiss()
        func(*args[:-1])

    def __init__(self, on_selection, mod_name, locations=[], title=default_title,
                 markup=False):
        bl = BoxLayout(orientation='vertical')

        text = textwrap.dedent('''
            A mod similar to {} has been found on disk.

            You can:
              1) Ignore it and download the whole mod from the internet (takes additional space).
              2) Copy its contents and then only download the missing files (faster, takes space).
              3) Let the launcher use that mod directory by creating a symbolic link (fastest, takes no space BUT may modify the original mod on your disk while synchronizing).

              ''') \
            .format(mod_name)

        la = Label(text=text, markup=markup, text_size=(570, None), size_hint=(1, 5))
        la.bind(on_ref_press=open_hyperlink)
        bl.add_widget(la)

        button = Button(text='Ignore and just download', size_hint_x=0.4, pos_hint={'center_x': 0.5})
        button.bind(on_release=partial(self.close_and_run, on_selection, None, 'ignore'))
        bl.add_widget(button)

        for location in locations:
            bl.add_widget(Widget())  # Spacer

            la = LabelB(text=location, markup=markup, text_size=(570, None), bcolor=(0, 0, 0, 0.3))
            la.bind(on_ref_press=open_hyperlink)
            bl.add_widget(la)

            horizontal_box = BoxLayout(orientation='horizontal', spacing=50, width=300)

            button = Button(text='Copy contents and synchronize', size=(100, 30))
            button.bind(on_release=partial(self.close_and_run, on_selection, location, 'copy'))
            horizontal_box.add_widget(button)

            button = Button(text='Create symbolic link and synchronize', size=(100, 30))
            button.bind(on_release=partial(self.close_and_run, on_selection, location, 'use'))
            horizontal_box.add_widget(button)

            bl.add_widget(horizontal_box)

        popup_height = 280 + (95 * len(locations))

        super(ModReuseBox, self).__init__(
            title=default_title, content=bl, size_hint=(None, None), size=(600, popup_height))

        # Bind a handler when the user closes the message
        self.custom_dismiss_uid = self.fbind('on_dismiss', lambda x: partial(on_selection, None, 'ignore')())
