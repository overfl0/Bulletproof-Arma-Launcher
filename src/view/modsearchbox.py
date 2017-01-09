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

import os
import textwrap

from functools import partial
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from view.chainedpopup import ChainedPopup
from view.behaviors import BubbleBehavior, HoverBehavior, DefaultButtonBehavior, HighlightBehavior
from view.filechooser import FileChooser
from view.messagebox import MessageBox
from view.modlist import ModList

default_title = ''


class HButton(HighlightBehavior, HoverBehavior, BubbleBehavior, Button):
    pass


class DefaultHoverButton(HighlightBehavior, HoverBehavior, BubbleBehavior, DefaultButtonBehavior, Button):
    pass


class ModSearchBox(ChainedPopup):
    def resize_box(self, container, la, size):
        container.height = sum(child.height for child in container.children)

    def is_directory_ok(self, path):
        return os.path.isdir(path)

    def _fbrowser_success(self, popup, instance):
        if instance.selection:
            selected = instance.selection[0]
        else:
            selected = instance.path

        if not self.is_directory_ok(selected):
            MessageBox('Not a directory or unreadable:\n{}'.format(selected)).open()
            return
        else:
            popup.dismiss()
            self.dismiss()
            self.on_selection('search', selected)

    def search_button_clicked(self, ignore):
        p = FileChooser(select_string='Search here', dirselect=True,
                        show_hidden=True, path=os.getcwd())

        p.browser.bind(on_success=partial(self._fbrowser_success, p))
        p.open()

    def ignore_button_clicked(self, ignore):
        self.dismiss()
        self.on_selection('download')

    def mod_location_selected(self, mod, new_path):
        if self.on_manual_path:
            self.on_manual_path(mod, new_path)

        if all (os.path.exists(mod.get_full_path()) for mod in self.mods):
            self.continue_button.text = 'OK'

    def __init__(self, on_selection, on_manual_path, mods, title=default_title):
        self.mods = mods
        self.on_selection = on_selection
        self.on_manual_path = on_manual_path

        bl = BoxLayout(orientation='vertical', size_hint=(1, None))
        bl.bind(size=self.update_vertical_size)

        text = textwrap.dedent('''\
            The following mods are missing and will need to be downloaded.
            Click on the directory icon to select a location manually.
            ''')
        la = Label(text=text, text_size=(570, None), size_hint=(1, None))  # , size_hint=(1, 2))
        la.bind(texture_size=la.setter('size'))
        la.bind(size=partial(self.resize_box, bl))
        bl.add_widget(la)

        self.scrollview = scrollview = ScrollView(size_hint=(1, None), height=300, bar_width=12, scroll_timeout=100, bar_inactive_color=[0.7, 0.7, 0.7, 0.5])  # , scroll_type=['bars'])
        scrollview.bind(size=partial(self.resize_box, bl))

        mods_list = ModList(mods, on_manual_path=self.mod_location_selected)
        mods_list.bind(size=partial(self.resize_box, bl))
        scrollview.add_widget(mods_list)

        bl.add_widget(scrollview)

        bl.add_widget(Widget(size_hint=(None, None), height=20))  # Spacer

        # Buttons
        horizontal_box = BoxLayout(orientation='horizontal', spacing=50, width=300, height=30, size_hint=(1, None))

        button1_bubble = textwrap.dedent('''\
            Select a directory to search for existing
            mods to use, to prevent redownloading.
            ''')
        button1 = DefaultHoverButton(text='Search on disk', size=(100, 30), size_hint=(1, None), bubble_text=button1_bubble)
        button1.bind(on_release=self.search_button_clicked)
        horizontal_box.add_widget(button1)

        button2_bubble = textwrap.dedent('''\
            Download all the mods listed above
            using your internet connection.
            ''')
        self.continue_button = button2 = HButton(text='Download missing', size=(100, 30), size_hint=(1, None), bubble_text=button2_bubble)
        button2.bind(on_release=self.ignore_button_clicked)
        horizontal_box.add_widget(button2)

        bl.add_widget(horizontal_box)

        super(ModSearchBox, self).__init__(
            title=default_title, content=bl, size_hint=(None, None), width=600, auto_dismiss=False)
