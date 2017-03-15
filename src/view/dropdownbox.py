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

import launcher_config
import kivy.utils

from functools import partial
from kivy.properties import ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.dropdown import DropDown
from view.labelb import LabelB
from view.behaviors import HoverBehavior


class DropdownBoxEntry(ButtonBehavior, HoverBehavior, LabelB):
    pass


class HoverBox(HoverBehavior, ButtonBehavior, BoxLayout):
    pass


class DropdownBox(HoverBox):
    values = ListProperty([])
    text = StringProperty('')
    default = StringProperty('')

    # Background color of the selected entry
    selection_color = ListProperty(kivy.utils.get_color_from_hex(launcher_config.dominant_color)[:3] + [0.8])

    @staticmethod
    def highlight_selection(selection_color, instance, hover):
        instance.bcolor = selection_color if hover and not instance.disabled else (0, 0, 0, 0.8)

    def updated_values(self, *args):
        self.dropdown.clear_widgets()

        for location in self.values:
            entry = DropdownBoxEntry(text=location, size_hint_y=None, height=25, bcolor=(0, 0, 0, 0.8))
            entry.bind(on_release=lambda entry: self.dropdown.select(entry.text))
            entry.bind(mouse_hover=partial(DropdownBox.highlight_selection, self.selection_color))
            self.dropdown.add_widget(entry)

        if not self.default:
            self.selected_text.text = self.values[0] if self.values else ''

    def updated_default(self, *args):
        if self.default:
            self.selected_text.text = self.default

    def __init__(self, entries=[], **kwargs):
        super(DropdownBox, self).__init__(orientation='horizontal', spacing=0, **kwargs)

        self.dropdown = DropDown()
        self.selected_text = LabelB(bcolor=(0, 0, 0, 0.3))

        self.dropdown.bind(on_select=lambda instance, x: setattr(self.selected_text, 'text', x))

        v_button = LabelB(text='V', bcolor=(0, 0, 0, 0.8), size_hint=(None, None))

        # Set the V button to a square size equal to the size of the Dropdown Box
        self.bind(size=lambda obj, size: v_button.setter('size')(v_button, (size[1], size[1])))
        self.bind(on_release=lambda x: self.dropdown.open(self))
        self.bind(mouse_hover=lambda instance, hover: partial(DropdownBox.highlight_selection, self.selection_color, v_button, hover)())
        self.bind(values=self.updated_values)
        self.bind(default=self.updated_default)

        self.add_widget(self.selected_text)
        self.add_widget(v_button)

        self.selected_text.bind(text=self.setter('text'))
        self.values = entries
