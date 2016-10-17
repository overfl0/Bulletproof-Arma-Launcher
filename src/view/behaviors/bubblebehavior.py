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
from kivy.core.window import Window
from kivy.uix.bubble import Bubble, BubbleButton

class BubbleBehavior(object):

    def __init__(self, **kwargs):
        super(BubbleBehavior, self).__init__(**kwargs)
        text = kwargs.get('bubble_text')
        arrow_pos = kwargs.get('arrow_pos', 'top_mid')

        if text:
            text = text.strip()
            self.bubble = bubble = Bubble(size_hint=(None, None))
            self.bubble_button = bubble_button = BubbleButton(markup=True, text=text)
            bubble_button.bind(texture_size=lambda obj, size: bubble.setter('size')(bubble, (size[0] + 30, size[1] + 30)))
            bubble.add_widget(bubble_button)

            self.bind(mouse_hover=partial(self.show_bubble, self, bubble, arrow_pos))

    @staticmethod
    def show_bubble(button, bubble, arrow_pos, instance, value):
        if value:
            Window.add_widget(bubble)
            bubble.arrow_pos = arrow_pos
            bubble.center_x = button.to_window(button.center_x, 0)[0]

            if arrow_pos.startswith('top'):
                bubble.top = button.to_window(0, button.y)[1]
            else:
                bubble.y = button.to_window(0, button.top)[1]

        else:
            Window.remove_widget(bubble)
