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


from functools import partial
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
    # Background color of the selected entry
    selection_color = (47 / 255., 167 / 255., 212 / 255., 0.8)

    def __init__(self, entries, **kwargs):
        super(DropdownBox, self).__init__(orientation='horizontal', spacing=0, **kwargs)

        self.dropdown = dropdown = DropDown()

        def highlight_selection(instance, hover):
            instance.bcolor = self.selection_color if hover else (0, 0, 0, 0.8)

        for location in entries:
            entry = DropdownBoxEntry(text=location, size_hint_y=None, height=25, bcolor=(0, 0, 0, 0.8))
            entry.bind(on_release=lambda entry: dropdown.select(entry.text))
            entry.bind(mouse_hover=highlight_selection)
            dropdown.add_widget(entry)

        selected_text = LabelB(text=entries[0] if entries else '', bcolor=(0, 0, 0, 0.3))  # text_size=(500, None)
        dropdown.bind(on_select=lambda instance, x: setattr(selected_text, 'text', x))
        dropdown.bind(on_select=lambda instance, x: setattr(self, 'text', x))

        button = LabelB(text='V', bcolor=(0, 0, 0, 0.8), size_hint=(None, None))  #  size_hint=(0.05, 1)

        # Set the V button to a square size equal to the size of the Dropdown Box
        self.bind(size=lambda obj, news: button.setter('size')(button, (news[1], news[1])))
        self.bind(on_release=lambda x: dropdown.open(self))
        self.bind(mouse_hover=lambda instance, hover: partial(highlight_selection, button, hover)())

        self.add_widget(button)

        self.add_widget(selected_text)

        self.text = selected_text.text
