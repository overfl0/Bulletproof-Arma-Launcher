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

from copy import copy

from kivy.core.window import Window
from kivy.uix.button import Button
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty
from kivy.clock import Clock



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
        self.last_text = None
        self.animation_states = ['...', '..', '.', '']
        self.text_animation_enabled = False

    def check_hover(self, instance, value):

        if (self.x <= value[0] <= self.x + self.width and
            self.y <= value[1] <= self.y + self.height):

            if self.mouse_hover == False:
                self.mouse_hover = True

        elif self.mouse_hover == True:
            self.mouse_hover = False

    def _on_mouse_hover(self, instance, value):
        if (value == True):
            self.background_normal_orig = self.background_normal
            self.background_normal = self.background_hover
        else:
            self.background_normal = self.background_normal_orig

    def enable_progress_animation(self):
        if not self.text_animation_enabled:
            self.last_text = self.text
            Clock.schedule_interval(self.do_progress_animation, 0.5)
            self.text_animation_enabled = True

    def disable_progress_animation(self):
        Clock.unschedule(self.do_progress_animation)
        self.text_animation_enabled = False

    def do_progress_animation(self, dt):
        st = self.animation_states.pop()
        self.text = self.last_text + st
        self.animation_states.insert(0, st)
