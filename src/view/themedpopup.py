# Bulletproof Arma Launcher
# Copyright (C) 2017 Lukasz Taczuk
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

import launcher_config
import kivy.utils

from kivy.uix.popup import Popup


class ThemedPopup(Popup):
    """Popup that has default values in config files."""

    config_separator_color = kivy.utils.get_color_from_hex(launcher_config.dominant_color)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('separator_color', self.config_separator_color)
        super(ThemedPopup, self).__init__(*args, **kwargs)
