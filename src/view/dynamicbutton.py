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

from collections import namedtuple
from hoverbutton import HoverButton
from kivy.logger import Logger


class DynamicButton(HoverButton):
    """
    Attempt at creating a dynamic button in Kivy.
    This button will change its text and other callbacks will be called
    depending on its state.
    """

    ButtonStates = namedtuple('ButtonStates', 'button_text button_callback')

    def __init__(self, **kwargs):
        super(DynamicButton, self).__init__(**kwargs)
        self.button_states = {None: self.ButtonStates('', None)}
        self.button_state = None

    def bind_state(self, state_name, button_text, button_callback):
        """Add a state that will show a text and call a callback when clicked."""
        self.button_states[state_name] = self.ButtonStates(button_text, button_callback)

    def on_release(self):
        """Get the right callback based on the button state and run it."""
        state_entry = self.button_states.get(self.button_state)

        if not state_entry:
            Logger.error('DynamicButton: No state: {}'.format(self.button_state))
            return

        if not state_entry.button_callback:
            Logger.info('DynamicButton: Button clicked but no callback was set for state {}'.format(self.button_state))
            return

        state_entry.button_callback(self)

    def set_button_state(self, name):
        """Mutator method."""
        try:
            button_state = self.button_states[name]

        except KeyError:
            Logger.error('DynamicButton: Trying to set state {} but such state does not exist!'.format(name))
            self.button_state = None
            self.text = '<no text>'
            self.texture_update()  # Update button texture for size calculation
            return

        self.button_state = name
        self.text = button_state.button_text
        self.texture_update()  # Update button texture for size calculation

    def get_button_state(self):
        """Accessor method."""
        return self.button_state
