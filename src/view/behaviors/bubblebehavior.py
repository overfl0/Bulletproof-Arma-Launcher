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

from functools import partial
from kivy.properties import StringProperty
from kivy.uix.bubble import Bubble, BubbleButton


class BubbleBehavior(object):

    bubble_text = StringProperty('')
    arrow_pos = StringProperty('top_mid')

    def __init__(self, *args, **kwargs):
        self.bind(bubble_text=self.create_bubble)
        self.bind(arrow_pos=self.create_bubble)

        self.bubble_callback = None

        super(BubbleBehavior, self).__init__(*args, **kwargs)

        bubble_text = kwargs.get('bubble_text')
        if bubble_text:
            self.bubble_text = bubble_text

        arrow_pos = kwargs.get('arrow_pos')
        if arrow_pos:
            self.arrow_pos = arrow_pos

    def create_bubble(self, instance, value):
        if not self.bubble_text:
            return

        if self.bubble_callback:
            self.funbind('mouse_hover', self.bubble_callback)

        text = self.bubble_text.strip()
        self.bubble = bubble = Bubble(size_hint=(None, None))
        self.bubble_button = bubble_button = BubbleButton(markup=True, text=text)
        bubble_button.bind(texture_size=lambda obj, size: bubble.setter('size')(bubble, (size[0] + 30, size[1] + 30)))
        bubble.add_widget(bubble_button)

        self.bubble_callback = partial(self.show_bubble, self, bubble, self.arrow_pos)

        # self.bind(mouse_hover=self.bubble_callback)
        self.fbind('mouse_hover', self.bubble_callback)

    @staticmethod
    def show_bubble(button, bubble, arrow_pos, instance, value):
        # Do not use Window as a parent for bubbles because if the widget's real
        # parent is removed, the widget is still visible.
        # Same for bubbles for objects inside ScrollViews.
        # TODO: Should find a way for bubbles to select arrow_pos automatically
        # depending on space available, instead.

        if value:
            button.add_widget(bubble)
            bubble.arrow_pos = arrow_pos
            bubble.center_x = button.center_x

            if arrow_pos.startswith('top'):
                bubble.top = button.y
            else:
                bubble.y = button.top

        else:
            button.remove_widget(bubble)
