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

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.properties import StringProperty, BooleanProperty, DictProperty
from kivy.logger import Logger


class StatusImage(BoxLayout):
    """
    Class can be used to show images for loading indication and other images

    It supports two new properties:

        hidden: set this property to true to hide the image
        source_map: a property specifying the possible used images for the box
                    to choose form. The dict must have a property called 'default',
                    which contains a path to the image which is loaded by default.
                    you can specify other key-path-pairs and then switch to them
                    using the set_image-method
    """
    hidden = BooleanProperty(False)
    source_map = DictProperty()

    def __init__(self, *args, **kwargs):
        super(StatusImage, self).__init__(*args, **kwargs)
        self.image = None
        self.bind(source_map=self.on_source_map_set)
        self.bind(hidden=self.on_hidden_set)
        self._hidden = False
        self.loaded_image_name = None
        self.orientation = 'vertical'

    def set_image(self, key):
        """
        set an image using a key specified in source_map

        if key is not found in source_map, nothing is set and an error
        is logged
        """
        source = self.source_map[key]

        if key not in self.source_map:
            Logger.error('StatusImage: your key "{}" is not in source_map'.format(key))
            return

        if not self.image:
            self.image = Image(source=source, id='loading_image', anim_delay=self.anim_delay)
            self.add_widget(self.image)
        else:
            self.image.source = source

        self.loaded_image_name = key

    def set_default_image(self):
        """set back the image to default"""
        self.set_image('default')

    def on_source_map_set(self, instance, source_dict):
        self.set_default_image()

    def on_hidden_set(self, instance, hidden):
        if self._hidden == hidden:
            return

        if hidden is True:
            self.remove_widget(self.image)
        else:
            self.add_widget(self.image)

        self._hidden = hidden

    def hide(self, on_error=False):
        '''Hide the status image widget.
        on_error - hide the widget even if it is showing an error icon.
        '''
        # This name is hardcoded for now. Probably should be rewritten in a better way
        if on_error is False and self.loaded_image_name == 'attention':
            return

        self.hidden = True

    def show(self):
        '''Show the status image widget.'''
        self.hidden = False
