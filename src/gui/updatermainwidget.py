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

import kivy
import kivy.app  # To keep PyDev from complaining
import os
import textwrap
import time

from kivy.clock import Clock
from kivy.logger import Logger
from kivy.uix.widget import Widget

from autoupdater import autoupdater
from autoupdater.autoupdater import UpdateException
from utils import paths
from utils import system_processes





class UpdaterMainWidget(Widget):
    def __init__(self, **kwargs):
        super(UpdaterMainWidget, self).__init__(**kwargs)
        self.controller = Controller(self)


class Controller(object):
    """docstring for UpdaterMainWidgetController"""
    install_timeout = 10

    def __init__(self, view):
        super(Controller, self).__init__()
        self.view = view
        Logger.info('init UpdaterMainWidgetController')

        self.app_settings = kivy.app.App.get_running_app().settings
        self.program_to_update = self.app_settings.get('update')
        # if self.program_to_update:
        #    self.program_to_update = os.path.realpath(self.program_to_update)

        Clock.schedule_interval(self.check_button_availability, 0.1)

    def set_status_string(self, status_string, error=True):
        wrapped_string = '\n'.join(textwrap.wrap(status_string, 55))
        self.view.ids.status_label.text = wrapped_string
        if error:
            Logger.error('Autoupdater: {}'.format(wrapped_string))
        else:
            Logger.info('Autoupdater: {}'.format(wrapped_string))

    def on_abort_button_release(self, button):
        Logger.info('Autoupdater: Aborting update')
        self.view.ids.status_label.text = 'Aborting ...'

        kivy.app.App.get_running_app().stop()

    def check_button_availability(self, dt):
        if 'abort_button' in self.view.ids:
            Clock.schedule_once(self.on_button_available, 0)
            return False

    def on_button_available(self, dt):
        self.set_status_string('Starting update process...', error=False)
        self.start_install_time = time.time()

        Clock.schedule_interval(self.try_install_update, 1)

    def try_install_update(self, dt):
        # Put everything into a big try-except block so that exceptions can be shown in a MessageBox
        # due to window size restrictions.
        try:
            # Check for timeout
            time_now = time.time()

            if time_now > self.start_install_time + self.install_timeout:
                raise UpdateException('Updater timed out.')

            # The file to update has to exist and be a file
            if self.program_to_update is None:
                raise UpdateException('No file to update!')

            if not os.path.isfile(self.program_to_update):
                raise UpdateException('File {} does not exist!'.format(self.program_to_update))

            if system_processes.file_running(self.program_to_update):
                self.set_status_string('Waiting for the launcher to stop...', error=False)
                return

            self.set_status_string('Copying the updated launcher...', error=False)
            autoupdater.perform_substitution(self.program_to_update)

            self.set_status_string('File copied successfully, running the new version now...', error=False)
            autoupdater.run_updated(self.program_to_update)

            kivy.app.App.get_running_app().stop()

        except UpdateException as ex:
            self.set_status_string(ex.message)
            return False  # Prevent the function from being called ever again
