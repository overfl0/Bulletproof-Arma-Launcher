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

import pygame

from kivy.app import App
from kivy.logger import Logger
from utils import browser
from utils.paths import get_resources_path
from utils.popupchain import PopupChain


class BaseApp(App):
    """docstring for BaseApp"""
    def __init__(self):
        super(BaseApp, self).__init__()
        self.popup_chain = PopupChain()

        try:
            pygame.mixer.init(44100, -16, 1, 512)

        except Exception as ex:
            Logger.error('BaseApp.__init__: Could not initialize sound: {}'.format(repr(ex)))

        self.sounds = {}
        self.load_sound('hover', self.resource_path('sounds/hover.wav'), 0.5)
        self.load_sound('click', self.resource_path('sounds/click.wav'))

    @staticmethod
    def resource_path(relative):
        """
        This method makes sure that the app can access resource path
        also if packed within a single executable
        """
        # Just use utils.paths.get_resources_path for less code replication
        return get_resources_path(relative)

    def load_sound(self, name, path, volume=None):
        """Load a sound associated with a name."""
        try:
            self.sounds[name] = pygame.mixer.Sound(path)

            if volume:
                self.sounds[name].set_volume(volume)

        except pygame.error:
            Logger.error('load_sound: Could not load sound: {}'.format(path))

    def play_sound(self, sound_name):
        """Play a sound associated with a name. Can be used in kv files."""
        try:
            sound = self.sounds[sound_name]
            if sound:
                sound.play()

        except KeyError:
            Logger.error('play_sound: Could not find sound: {}'.format(sound_name))

    def open_hyperlink(self, path):
        """Just open the given url in a browser.
        To open paths on the local filesystem special handling is needed.
        """

        if path is None:
            return

        browser.open_hyperlink(path)
