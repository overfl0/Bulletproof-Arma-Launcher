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

class HighlightBehavior(object):
    """Highlights the button when mouse_hover is True
    """

    def light_the_button(self, instance, hover):
        if hover:
            instance.background_color = (1.5, 1.5, 1.5, 1.5)
        else:
            instance.background_color = (1, 1, 1, 1)

    def __init__(self, **kwargs):
        super(HighlightBehavior, self).__init__(**kwargs)

        self.bind(mouse_hover=self.light_the_button)
