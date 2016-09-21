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

from kivy.graphics import Color, Line

class DefaultButtonBehavior(object):
    """Behavior that adds a border around the button much like a default choice.
    """

    def __init__(self, **kwargs):
        super(DefaultButtonBehavior, self).__init__(**kwargs)

        with self.canvas.after:
            Color(1, 1, 1, 0.7)
            self.default_border_line = Line(rectangle=
                (self.x + 1, self.y + 1, self.width - 3, self.height - 1), width=1.1)

        self.bind(pos=self.update_default_border_line)
        self.bind(size=self.update_default_border_line)

    def update_default_border_line(self, *args):
        self.default_border_line.rectangle = \
            (self.x + 1, self.y + 1, self.width - 3, self.height - 1)

'''
# http://robertour.com/2015/07/15/kivy-label-or-widget-with-background-color-property/
from kivy.uix.button import Button
from kivy.properties import ListProperty

from kivy.factory import Factory
from kivy.lang import Builder

Builder.load_string("""
<DefaultButton>:
  canvas.after:
    Color:
      rgba: 1,1,1,0.7
    Line:
      rectangle: self.x+1,self.y+1,self.width-3,self.height-1
""")

class DefaultButton(Button):
    pass

Factory.register('DefaultButton', module='DefaultButton')
'''
