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

from kivy.properties import ListProperty
from kivy.graphics import Color, Rectangle


class BgcolorBehavior(object):
    """Behavior that adds a border around the button much like a default choice."""

    bcolor = ListProperty([1, 1, 1, 0])

    def __init__(self, *args, **kwargs):
        super(BgcolorBehavior, self).__init__(*args, **kwargs)

        if 'bcolor' in kwargs:
            self.bcolor = kwargs['bcolor']

        with self.canvas.before:
            Color(*self.bcolor)

            self.bgrectangle = Rectangle(pos=(self.x, self.y), size=(self.width, self.height))

        self.bind(pos=self.update_background_rectangle)
        self.bind(size=self.update_background_rectangle)

    def update_background_rectangle(self, *args):
        self.bgrectangle.pos = self.to_widget(*self.to_window(*self.pos))
        self.bgrectangle.size = self.size
