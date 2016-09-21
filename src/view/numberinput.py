# Bulletproof Arma Launcher
# Copyright (C) 2016 Sascha Ebert
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

"""The NumberInput field"""
import re

from kivy.logger import Logger
from kivy.uix.textinput import TextInput


class NumberInput(TextInput):

    # NOTE: The use of negative numbers is problematic now. It is possible to write "12-34"
    pat = re.compile('[0-9]+')

    def insert_text(self, substring, from_undo=False):
        if self.pat.match(substring):
            # Logger.debug('Matched substring: {} :: Text is {}'.format(substring, self.text))
            return super(NumberInput, self).insert_text(substring, from_undo=from_undo)
        else:
            return super(NumberInput, self).insert_text('', from_undo=from_undo)

    # def on_focus(self, inputfield, focus):
    #     """property handler"""
    #     if self.text == '' and not focus:
    #         inputfield.text = "0"

    def get_value(self):
        """get the text as typed number, in this case int"""
        if self.text == '':
            return 0
        else:
            try:
                return int(self.text)
            except ValueError:
                Logger.warn('NumberImput: Could not convert text input. Returning 0')
                return 0
