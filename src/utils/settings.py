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

import argparse

class Settings(object):
    """docstring for Settings"""
    def __init__(self, argv):
        super(Settings, self).__init__()

        self.parser = None
        self.settings_data = None

        self.parse_args(argv)

    def parse_args(self, argv):
        self.parser = argparse.ArgumentParser()

        self.parser.add_argument("-s", "--self-update",
            help="run the self updater", action="store_true")

        self.settings_data = self.parser.parse_args(argv)

        print self.settings_data

    def get(self, key):
        """retrieve a property from the settings namespace
        if the property does not exists return None"""

        if key in self.settings_data:
            return getattr(self.settings_data, key)
        else:
            return None
