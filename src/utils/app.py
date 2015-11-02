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

import sys, os

from kivy.app import App

class BaseApp(App):
    """docstring for BaseApp"""
    def __init__(self):
        super(BaseApp, self).__init__()

    @staticmethod
    def resource_path(relative):
        """
        This method makes sure that the app can access resource path
        also if packed within a single executable
        """
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, relative)

        base_path = os.path.dirname(os.path.realpath(sys.argv[0]))
        return os.path.realpath(os.path.join(base_path, '../resources', relative))
