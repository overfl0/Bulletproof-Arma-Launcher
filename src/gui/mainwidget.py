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
from gui.messagebox import MessageBox

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
        return  # Disable this for the alpha release
        raise TestError('This is an test error')

    def on_next_frame(self, dt):
        # Only show the notification in alpha branch
        alpha_text = """Welcome to the Tactical Battlefield Mod launcher!

This is an early alpha version of the launcher and as such it WILL contain bugs!
Although we have made every effort possible to ensure safe use of the launcher,
we cannot guarantee it.

Users of this launcher in alpha version are expected to be technically
knowledgeable and capable of fixing their Arma 3 installation should
something go awry.
If you do not meet the above criterion, stop using this launcher now!

Don't forget to report bugs at http://tacbf.com or at
https://bitbucket.org/tacbf_launcher/tacbf_launcher/issues


                                                                               -- The TacBF launcher team
"""

        alpha_title = 'Tactical Battlefield Mod launcher (Alpha)'
        alpha_box = MessageBox(text=alpha_text, title=alpha_title)
        Logger.info('MainWidget: opening alpha popup')
        alpha_box.open()
