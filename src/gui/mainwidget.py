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

import io
import kivy.app
import os

from functools import partial
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.logger import Logger
from kivy.network.urlrequest import UrlRequest
from kivy.uix.widget import Widget
from utils import filecache
from utils.paths import get_resources_path


class MainWidget(Widget):
    """
    View Class
    """
    def __init__(self, **kwargs):
        super(MainWidget, self).__init__(**kwargs)
        self.controller = Controller(self)

class Controller(object):
    def __init__(self, widget):
        super(Controller, self).__init__()
        self.view = widget
        self.settings = kivy.app.App.get_running_app().settings
        kivy.app.App.get_running_app().main_widget = widget

        self.last_background_url = None  # Race condition prevention
        self.anim = None  # Race condition prevention

        # this effectively calls on_next_frame, when the view is ready
        Clock.schedule_once(self.on_next_frame, 0)

    def on_next_frame(self, dt):
        """Called once, when the view is ready."""

        background_path = self.settings.get('last_custom_background')
        Logger.info('MainWidget: Settings background to: {}'.format(background_path))
        self.set_background_path(background_path, use_transition=False)

    def _background_fetch_failure(self, request, result):
        """Callback called when a background image fetch failed."""
        Logger.error('Background: Fetching the background image failed')

    def _background_fetch_error(self, request, error):
        """Callback called when a background image fetch raised an internal error."""
        Logger.info('Background: Fetching the background image raised an error: {}'.format(error))

    def _background_fetch_success(self, url, request, result):
        """Callback called when a background image fetch succeeded."""
        Logger.info('Background: Fetching the background image succeeded! {}'.format(url))

        # Check if the image data is correct and can actually be loaded
        try:
            im = CoreImage(io.BytesIO(result), ext=url.split('.')[-1])

        except Exception as ex:
            Logger.error('Background: The image downloaded could not be correctly loaded: {}'.format(repr(ex)))
            im = None

        if im:
            filecache.save_file(url, result)

            # If a new request has been made in the meantime, don't change the background!
            if url == self.last_background_url:
                self.set_background_path(filecache.map_file(url))


    def _pop_background(self, animation, widget):
        """Switch the background images so that a new image can be shown in the
        background, in the future.
        """

        self.view.ids.background.source = self.view.ids.background_new.source
        self.view.ids.background_new.opacity = 0

        self.anim = None

    def set_background_path(self, path, use_transition=True):
        """Set the background to a file on disk pointed by the path."""

        self.settings.set('last_custom_background', path)

        if path is None:
            path = get_resources_path('images/back.png')

        if self.view.ids.background.source == path and self.anim is None:
            Logger.info('Background: The requested background is already used. Not doing anything.')
            return

        Logger.info('Background: setting background to: {}'.format(path))

        if not os.path.isfile(path):
            Logger.info('Background: Trying to set the background to an nonexistent file: {}'.format(
                path))
            return

        self.view.ids.background_new.opacity = 0
        if use_transition:
            self.view.ids.background_new.source = path

            self.anim = Animation(opacity=1, transition='linear', duration=2)
            self.anim.bind(on_complete=self._pop_background)

            Animation.cancel_all(self.view.ids.background_new)
            self.anim.start(self.view.ids.background_new)

        else:
            self.view.ids.background.source = path

    def set_background(self, url):
        """Set the background to a file pointed by the url. The file will be
        fetched if it is not already cached.

        If url is None, the default background will be used.
        """

        self.last_background_url = url

        if url is None:
            Logger.info('Background: No background set')
            self.set_background_path(None)
            return

        background_path = filecache.map_file(url)
        if os.path.isfile(background_path):
            Logger.info('Background: Background already fetched. Reusing cached data.')
            self.set_background_path(background_path)

        else:
            Logger.info('Background: Fetching url: {}'.format(url))
            self.url_request = UrlRequest(url,
                       on_success=partial(self._background_fetch_success, url),
                       on_error=self._background_fetch_error,
                       decode=False,
                       timeout=30)
