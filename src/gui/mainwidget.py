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

import kivy.app
import os
import textwrap
import time

from kivy.uix.widget import Widget
from kivy.logger import Logger
from kivy.clock import Clock

from view.errorpopup import ErrorPopup
from view.messagebox import MessageBox

from utils.devmode import devmode


class TestError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


def test_exc_in_process():
    """function for testing if the exceptions gets rethrown into
    the kivy main process
    """
    pass
    time.sleep(2)
    raise TestError('This is a test error')


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

        # this effectively calls on_next_frame, when the view is ready
        Clock.schedule_once(self.on_next_frame, 0)

    def on_testpopupbutton_release(self, btn):
        return  # Disable this for the alpha release
        # raise TestError('This is an test error')
        # self.get_status_image().set_image('attention')

    def on_next_frame(self, dt):
        # TODO: Remove this in several months when this will not be relevant anymore
        old_dir = self.settings.launcher_default_basedir_old()

        directory_text = textwrap.dedent('''
            *********************************************************
            * IMPORTANT!
            *********************************************************

            [color=FF0000]All settings have been reset for version 1.0![/color]

            Go to OPTIONS and verify whether everything is in order, especially
            the "Mods directory"!

            *********************************************************
            * IMPORTANT!
            *********************************************************

            Please remove [ref={}][color=3572b0]the old directory (click here!)[/color][/ref] manually.
            It is not deleted automatically for safety reasons

            This is a one time message and will not appear again.
            '''.format(old_dir))

        directory_title = 'IMPORTANT! Action needed!'
        directory_box = MessageBox(text=directory_text, title=directory_title, markup=True)

        if os.path.exists(old_dir):
            notice_already = self.settings.get('basedir_change_notice')
            if not notice_already:
                self.settings.set('basedir_change_notice', 1)
                directory_box.chain_open()

    def get_status_image(self):
        """retrieve the status image from the tree"""
        return self.view.ids.main_screen_manager.get_screen('install_screen').ids.status_image
