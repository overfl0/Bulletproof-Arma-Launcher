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

import kivy.app

from kivy.properties import BooleanProperty, ListProperty
from kivy.uix.button import Button
from view.behaviors import HoverBehavior


class HoverButton(HoverBehavior, Button):
    # Background color of the selected entry
    color_normal = ListProperty([1, 1, 1, 1])
    color_hover = ListProperty([])
    # bgcolor_normal = ListProperty([1, 1, 1, 1])
    bgcolor_normal = ListProperty([])
    bgcolor_hover = ListProperty([])
    force_hover = BooleanProperty(False)

    def __init__(self, *args, **kwargs):
        super(HoverButton, self).__init__(*args, **kwargs)
        self.bind(mouse_hover=self.on_hover)
        self.is_hovered = False
        self.bind(text=self.on_text)
        self.bind(force_hover=self.on_force_hover)

    def on_text(self, instance, text):
        try:
            # Prevent infinite loop
            if instance.text.startswith(instance.text_prefix):
                return

            instance.text = instance.text_prefix + text

        except AttributeError:  # No text_prefix
            pass

    def on_force_hover(self, *args):
        self.on_hover(self, self.is_hovered, play_sound=False)

    def on_hover(self, instance, hover, play_sound=True):

        self.is_hovered = hover
        if self.disabled:
            return

        if self.force_hover:
            hover = True

        if hover:
            if play_sound:
                kivy.app.App.get_running_app().play_sound('hover')

            if self.color_hover:
                self.color = self.color_hover

            if self.bgcolor_hover:
                self.background_color = self.bgcolor_hover

        else:
            self.color = self.color_normal
            self.background_color = self.bgcolor_normal

    def disable(self):
        """Helper function allowing for setting breakpoints on this action."""
        if self.disabled:
            return

        self.disabled = True
        self.background_color = self.bgcolor_normal

    def enable(self):
        """Helper function allowing for setting breakpoints on this action."""
        if not self.disabled:
            return

        self.disabled = False

        # Force on_hover to set the right background in case the button was
        # invisible and optionally to play a sound if the button is hovered now.
        self.on_hover(self, self.is_hovered)
