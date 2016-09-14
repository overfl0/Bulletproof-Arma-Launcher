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
from kivy.uix.bubble import Bubble, BubbleButton

class BubbleBehavior(object):

    def __init__(self, **kwargs):
        super(BubbleBehavior, self).__init__(**kwargs)
        text = kwargs.get('bubble_text')

        if text:
            self.bubble = bubble = Bubble()
            self.bubble_button = bubble_button = BubbleButton(markup=True, text=text)
            bubble_button.bind(texture_size=lambda obj, news: bubble.setter('size')(bubble, (news[0] + 30, news[1] + 30)))  # b.setter('text_size'))
            bubble.add_widget(bubble_button)

            self.bind(mouse_hover=partial(self.show_bubble, self, bubble))

    @staticmethod
    def show_bubble(button, bubble, instance, value):
        if value:
            button.add_widget(bubble)
            bubble.center_x = button.center_x
            bubble.top = button.y
            bubble.arrow_pos = 'top_mid'

        else:
            button.remove_widget(bubble)
