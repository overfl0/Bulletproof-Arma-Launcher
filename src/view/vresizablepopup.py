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

import kivy

from kivy.clock import Clock
from kivy.logger import Logger
from kivy.uix.widget import Widget
from view.themedpopup import ThemedPopup


class VResizablePopup(ThemedPopup):
    """Popup that allows to resize itself vertically.
    This is a workaround for Kivy. Maybe there is another simpler way?
    """

    def __init__(self, *args, **kwargs):
        # Force size_hint_y to None
        kwargs['size_hint_y'] = None
        if 'size_hint' in kwargs:
            kwargs['size_hint'] = kwargs['size_hint'][0], None

        super(VResizablePopup, self).__init__(*args, **kwargs)
        self.bind(content=self._on_update_content)

    def _on_update_content(self, me, new_content):
        if self._get_decoration_size():
            self.height = new_content.height + self._get_decoration_size()

    def _get_decoration_size(self):
        if self.height == self._container.height:
            return None

        decoration_size = getattr(self, '_decoration_size', self.height - self._container.height)
        self._decoration_size = decoration_size
        return decoration_size

    def update_vertical_size(self, *args):
        """Force an update of the popup's contents that will resize the height
        of that popup.
        """
        if self._get_decoration_size() is None:
            Logger.info('Vpopup: Decorations size unknown, rescheduling resizing process')
            Clock.schedule_once(self.update_vertical_size, -1)
        else:
            self._do_content_update()

    def _do_content_update(self):
        tmp = self.content
        self.content = Widget(size=(100, 100), size_hint=(None, None))
        self.content = tmp
