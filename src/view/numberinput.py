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

import re

from kivy.logger import Logger
from kivy.uix.textinput import TextInput

class NumberInput(TextInput):

    pat = re.compile('[0-9]+')

    def insert_text(self, substring, from_undo=False):
        if self.pat.match(substring):
            Logger.debug('Matched substring: {}'.format(substring))
            return super(NumberInput, self).insert_text(substring, from_undo=from_undo)
        else:
            return super(NumberInput, self).insert_text('', from_undo=from_undo)
