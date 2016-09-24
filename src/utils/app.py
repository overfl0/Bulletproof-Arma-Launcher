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

from kivy.app import App
from utils.paths import get_resources_path
from utils.popupchain import PopupChain


class BaseApp(App):
    """docstring for BaseApp"""
    def __init__(self):
        super(BaseApp, self).__init__()
        self.popup_chain = PopupChain()

    @staticmethod
    def resource_path(relative):
        """
        This method makes sure that the app can access resource path
        also if packed within a single executable
        """
        # Just use utils.paths.get_resources_path for less code replication
        return get_resources_path(relative)
