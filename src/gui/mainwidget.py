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
import time

from kivy.uix.widget import Widget
from kivy.logger import Logger
from kivy.clock import Clock

from view.errorpopup import ErrorPopup
from gui.alphanotification import AlphaNotification

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
    raise TestError('This is an test error')

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

        # this effectivly calls on_next_frame, when the view is ready
        Clock.schedule_once(self.on_next_frame, 0)

    def on_testpopupbutton_release(self, btn):
        raise TestError('This is an test error')

    def on_next_frame(self, dt):
        a = AlphaNotification()
        Logger.info('MainWidget: running alphapopup')
        a.open()
