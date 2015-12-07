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

from __future__ import unicode_literals

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.properties import StringProperty, BooleanProperty

class StatusImage(BoxLayout):
    """
    Class can be used to show images for loading indication
    """
    source = StringProperty('')
    hidden = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(StatusImage, self).__init__(**kwargs)
        self.image = None
        self.bind(source=self.on_source_set)
        self.bind(hidden=self.on_hidden_set)
        self._hidden = False

    def on_source_set(self, instance, source):
        if not self.image:
            self.image = Image(source=source, id='loading_image', anim_delay=0.05)
            self.add_widget(self.image)
        else:
            self.image.source = source

    def on_hidden_set(self, instance, hidden):
        if self._hidden == hidden:
            return

        if hidden == True:
            self.remove_widget(self.image)
        else:
            self.add_widget(self.image)

        self._hidden = hidden

    def hide(self):
        pass

    def show(self):
        pass
