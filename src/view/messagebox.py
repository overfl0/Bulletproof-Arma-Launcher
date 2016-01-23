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

import sys

from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from view.chainedpopup import ChainedPopup

default_title = """Message"""


def open_hyperlink(obj, ref):
    import webbrowser

    if ref[1:].startswith(':\\'):  # C:\, D:\, etc...
        ref = ref.encode(sys.getfilesystemencoding())

    webbrowser.open(ref)


class MessageBox(ChainedPopup):
    def __init__(self, text, title=default_title, markup=False):
        bl = BoxLayout(orientation='vertical')
        la = Label(text=text, size_hint_y=0.8, markup=markup)
        la.bind(on_ref_press=open_hyperlink)
        button = Button(text="Ok", size_hint_y=0.2)
        button.bind(on_release=self.dismiss)

        bl.add_widget(la)
        bl.add_widget(button)

        super(MessageBox, self).__init__(
            title=title, content=bl, size_hint=(None, None), size=(600, 500))
