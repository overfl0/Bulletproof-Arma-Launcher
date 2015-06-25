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

import argparse, os

from kivy.logger import Logger

from utils.registry import Registry

class Settings(object):
    """docstring for Settings"""

    # path to the registry entry which holds the users document path
    _USER_DOCUMENT_PATH = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"

    # set this to true to show a popup containing exceptions
    # if one occurres
    _EXC_POPUP = True

    def __init__(self, argv):
        super(Settings, self).__init__()

        self.parser = None
        self.settings_data = None

        self.parse_args(argv)

        self.settings_data.exc_popup = self._EXC_POPUP

        # create the launcher basedir if neccessary
        # take the the command line param first if present
        if not self.settings_data.launcher_basedir:
            self.settings_data.launcher_basedir = self._get_launcher_basedir_from_reg()

        launcher_moddir = self.get_launcher_moddir()
        launcher_basedir = self.get_launcher_basedir()

        if not os.path.isdir(launcher_basedir):
            Logger.debug('Settings: Creating basedir - {}'.format(launcher_basedir))
            os.mkdir(launcher_basedir)

        if not os.path.isdir(launcher_moddir):
            Logger.debug('Settings: Creating mod dir - {}'.format(launcher_moddir))
            os.mkdir(launcher_moddir)

        Logger.debug("Settings: Launcher will use basedir: " + self.get_launcher_basedir())
        Logger.debug("Settings: Launcher will use moddir: " + self.get_launcher_moddir())

    def _get_launcher_basedir_from_reg(self):
        """retreive users document folder from the registry"""
        path = None
        user_docs = Registry.ReadValueCurrentUser(Settings._USER_DOCUMENT_PATH, 'Personal')
        path = os.path.join(user_docs, 'TacBF Launcher')

        return path

    def get_launcher_basedir(self):
        return self.settings_data.launcher_basedir

    def get_launcher_moddir(self):
        return os.path.join(self.get_launcher_basedir(), 'mods')
        return path

    def parse_args(self, argv):
        self.parser = argparse.ArgumentParser()

        self.parser.add_argument("-u", "--update", metavar='OLD_EXECUTABLE',
            help="Run the self updater. OLD_EXECUTABLE is the file to be updated.")

        self.parser.add_argument("-d", "--launcher-basedir",
            help="Specify the basedir for the launcher")

        self.parser.add_argument("-r", "--run-updated", action='store_true',
            help="Dummy switch to test autoupdate")

        self.settings_data = self.parser.parse_args(argv)

        print self.settings_data

    def get(self, key):
        """retrieve a property from the settings namespace
        if the property does not exists return None"""

        if key in self.settings_data:
            return getattr(self.settings_data, key)
        else:
            return None
