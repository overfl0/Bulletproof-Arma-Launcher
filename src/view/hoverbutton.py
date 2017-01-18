# Bulletproof Arma Launcher
# Copyright (C) 2016 Sascha Ebert
# Copyright (C) 2017 Lukasz Taczuk
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

from kivy.properties import ListProperty
from kivy.uix.button import Button
from view.behaviors import HoverBehavior


class HoverButton(HoverBehavior, Button):
    # Background color of the selected entry
    # selection_color = (47 / 255., 167 / 255., 212 / 255., 0.8)
    color_normal = ListProperty([1, 1, 1, 1])
    color_hover = ListProperty([])
    # bgcolor_normal = ListProperty([1, 1, 1, 1])
    bgcolor_normal = ListProperty([])
    bgcolor_hover = ListProperty([])

    def __init__(self, *args, **kwargs):
        super(HoverButton, self).__init__(*args, **kwargs)
        self.bind(mouse_hover=self.on_hover)

    def on_hover(self, instance, hover):

        if hover and not self.disabled:
            if self.color_hover:
                self.color = self.color_hover

            if self.bgcolor_hover:
                self.background_color = self.bgcolor_hover
        else:
            self.color = self.color_normal
            self.background_color = self.bgcolor_normal

    def disable(self):
        """Helper function allowing for setting breakpoints on this action."""
        self.disabled = True

    def enable(self):
        """Helper function allowing for setting breakpoints on this action."""
        self.disabled = False
