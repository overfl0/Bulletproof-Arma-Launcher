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

import textwrap

from dropdownbox import DropdownBox
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from view.chainedpopup import ChainedPopup
from view.behaviors import BubbleBehavior, HoverBehavior, DefaultButtonBehavior, HighlightBehavior


default_title = ''


class HButton(HighlightBehavior, HoverBehavior, BubbleBehavior, Button):
    pass


class DefaultHoverButton(HighlightBehavior, HoverBehavior, BubbleBehavior, DefaultButtonBehavior, Button):
    pass


class ModReuseBox(ChainedPopup):
    def __init__(self, on_selection, mod_name, locations=None, title=default_title):
        if locations is None:
            locations = []

        bl = BoxLayout(orientation='vertical')

        text = textwrap.dedent('''
            The mod [b]{}[/b] has been found in the following location(s):
            ''') \
            .format(mod_name)

        la = Label(text=text, markup=True, text_size=(570, None) , size_hint=(1, 2))
        bl.add_widget(la)

        dropdown_box = DropdownBox(locations)
        bl.add_widget(dropdown_box)

        bl.add_widget(Widget(size_hint=(1, 0.5)))  # Spacer

        # Buttons
        horizontal_box = BoxLayout(orientation='horizontal', spacing=50, width=300)

        button1_bubble = textwrap.dedent('''\
            Use that mod directly (fastest, takes almost
            no additional space [color=ff3333]but may modify the
            original mod on your disk while synchronizing[/color]).''')
        button1 = DefaultHoverButton(text='Use that mod', size=(100, 30), bubble_text=button1_bubble)
        button1.bind(on_release=self.dismiss)
        button1.bind(on_release=lambda x: on_selection(mod_name, dropdown_box.text, 'use'))
        horizontal_box.add_widget(button1)

        button2_bubble = textwrap.dedent('''\
            Create a local copy of the mod and only download
            the missing files (faster, takes additional space).''')
        button2 = HButton(text='Copy it', size=(100, 30), bubble_text=button2_bubble)
        button2.bind(on_release=self.dismiss)
        button2.bind(on_release=lambda x: on_selection(mod_name, dropdown_box.text, 'copy'))
        horizontal_box.add_widget(button2)

        button3_bubble = textwrap.dedent('''\
            Do not use the location(s) above.
            You can search for this mod in
            another location later.
            ''')
        button3 = HButton(text='Skip', size=(100, 30), bubble_text=button3_bubble)
        button3.bind(on_release=self.dismiss)
        button3.bind(on_release=lambda x: on_selection(mod_name, dropdown_box.text, 'ignore'))
        horizontal_box.add_widget(button3)

        bl.add_widget(horizontal_box)

        popup_height = 180

        super(ModReuseBox, self).__init__(
            title=default_title, content=bl, size_hint=(None, None), size=(600, popup_height), auto_dismiss=False)
