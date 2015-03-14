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

from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty

class HoverButton(Button):
    """
    lightly extended button implementation

    It supports hover state for now
    """
    mouse_hover = BooleanProperty(False)
    background_hover = StringProperty('')

    def __init__(self, **kwargs):
        super(HoverButton, self).__init__(**kwargs)
        Window.bind(mouse_pos=self.check_hover)

        self.bind(mouse_hover=self._on_mouse_hover)

        self.background_normal_orig = ''

    def check_hover(self, instance, value):

        if (self.x <= value[0] <= self.x + self.width and
            self.y <= value[1] <= self.y + self.height):

            if self.mouse_hover == False:
                self.mouse_hover = True

        elif self.mouse_hover == True:
            self.mouse_hover = False

    def _on_mouse_hover(self, instance, value):
        print 'mouse_hover changed', value
        if (value == True):
            print 'switching to bg hover', self.background_hover
            self.background_normal_orig = self.background_normal
            self.background_normal = self.background_hover
        else:
            self.background_normal = self.background_normal_orig
