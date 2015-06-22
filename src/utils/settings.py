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
from utils.data.model import Model

class Settings(Model):
    """docstring for Settings"""

    # path to the registry entry which holds the users document path
    _USER_DOCUMENT_PATH = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"

    # set this to true to show a popup containing exceptions
    # if one occurres
    _EXC_POPUP = True

    fields = [
        {'name': 'use_exception_popup', 'defaultValue': True},
        {'name': 'self_update', 'defaultValue': False},
        {'name': 'launcher_basedir'}
    ]

    def __init__(self, argv):
        super(Settings, self).__init__()

        # set default values

        # parse arguments
        self.parser = None
        self.parse_args(argv)

        Logger.info('Settings: loaded args: ' + str(self.data))


        # create the launcher basedir if neccessary
        # take the the command line param first if present
        if not self.get('launcher_basedir'):
            self.set('launcher_basedir', self._get_launcher_basedir_from_reg())

        launcher_moddir = self.get_launcher_moddir()
        launcher_basedir = self.get_launcher_basedir()

        if not os.path.isdir(launcher_basedir):
            Logger.debug('Settings: Creating basedir - {}'.format(launcher_basedir))
            os.mkdir(launcher_basedir)

        if not os.path.isdir(launcher_moddir):
            Logger.debug('Settings: Creating mod dir - {}'.format(launcher_moddir))
            os.mkdir(launcher_moddir)

        Logger.info("Settings: Launcher will use basedir: " + self.get_launcher_basedir())
        Logger.info("Settings: Launcher will use moddir: " + self.get_launcher_moddir())

    def _get_launcher_basedir_from_reg(self):
        """retreive users document folder from the registry"""
        path = None
        user_docs = Registry.ReadValueCurrentUser(Settings._USER_DOCUMENT_PATH, 'Personal')
        path = os.path.join(user_docs, 'TacBF Launcher')

        return path

    def get_launcher_basedir(self):
        return self.get('launcher_basedir')

    def get_launcher_moddir(self):
        return os.path.join(self.get_launcher_basedir(), 'mods')

    def parse_args(self, argv):
        self.parser = argparse.ArgumentParser()

        self.parser.add_argument("-s", "--self-update",
            help="run the self updater", action="store_true")

        self.parser.add_argument("-d", "--launcher-basedir",
            help="specify the basedir for the launcher")

        settings_data = self.parser.parse_args(argv)

        for f in self.fields:
            value  = getattr(settings_data, f['name'], None)
            if value != None:
                self.set(f['name'], value)
