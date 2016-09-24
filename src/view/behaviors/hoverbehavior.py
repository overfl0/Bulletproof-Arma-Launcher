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

from kivy.properties import BooleanProperty
from kivy.core.window import Window

class HoverBehavior(object):

    mouse_hover = BooleanProperty(False)

    def __init__(self, **kwargs):
        Window.bind(mouse_pos=self.on_mouse_pos)
        super(HoverBehavior, self).__init__(**kwargs)

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return

        pos = args[1]

        # The property mouse_hover should be set only when it changes
        # So all the bound functions are called only when needed
        if self.collide_point(*self.to_widget(*pos)):
            if self.mouse_hover is not True:
                self.mouse_hover = True

        else:
            if self.mouse_hover is not False:
                self.mouse_hover = False
