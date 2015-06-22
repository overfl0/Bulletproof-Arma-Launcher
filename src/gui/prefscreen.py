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

import kivy
from arma.arma import Arma, ArmaNotInstalled
from gui.messagebox import MessageBox
from kivy.clock import Clock

from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.logger import Logger

class PrefScreen(Screen):
    """
    View Class
    """
    def __init__(self, **kwargs):
        super(PrefScreen, self).__init__(**kwargs)
        self.controller = Controller(self)

class Controller(object):
    def __init__(self, widget):
        super(Controller, self).__init__()
        self.view = widget
        Logger.info('PrefScreen: init controller')

        Clock.schedule_interval(self.check_childs, 0)

    def check_childs(self, dt):
        Logger.info('PrefScreen: got ids: ' + str(self.view.ids))

        return False
