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

from utils.data.jsonstore import JsonStore
from utils.critical_messagebox import MessageBox

class LauncherConfig(Model):
    """Container class for storing configuration"""

    fields = [
        {'name': 'use_exception_popup', 'defaultValue': False},
        {'name': 'self_update', 'defaultValue': False},
        {'name': 'launcher_basedir'},
        {'name': 'launcher_moddir'},
    ]

    def __init__(self):
        super(LauncherConfig, self).__init__()


class Settings(object):
    """docstring for Settings"""

    # path to the registry entry which holds the users document path
    _USER_DOCUMENT_PATH = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"

    # the folder name where everything gets store. This will get the last
    # part of the launcher_basedir
    _LAUNCHER_DIR = 'TacBF Launcher'


    def __init__(self, argv):
        super(Settings, self).__init__()

        # get the basedir for config files. This has to be the same everytime
        self.config_path = os.path.join(self._get_launcher_basedir_from_reg(), 'config.json')

        # init LauncherConfig
        self.launcher_config = LauncherConfig()


        # load config
        try:
            store = JsonStore(self.config_path)
            self.launcher_config = store.load(self.launcher_config, update=True)
        except:
            Logger.warn('Settings: Launcher config could not be loaded')

        # parse arguments
        self.parser = None
        self.parse_args(argv)

        Logger.info('Settings: loaded args: ' + str(self.launcher_config.data))

        self.reinit()

    def reinit(self):
        """recreate directories if something changed"""

        # create the launcher basedir if neccessary
        # take the the command line param first if present
        if not self.launcher_config.get('launcher_basedir'):
            self.launcher_config.set('launcher_basedir', self._get_launcher_basedir_from_reg())

        launcher_moddir = self.get_launcher_moddir()
        launcher_basedir = self.get_launcher_basedir()

        if not os.path.isdir(launcher_basedir):
            Logger.info('Settings: Creating basedir - {}'.format(launcher_basedir))
            try:
                os.mkdir(launcher_basedir)
            except OSError:
                reg_basedir = self._get_launcher_basedir_from_reg()
                # TODO: Show a regular message box, not a win32 message box
                MessageBox("Could not create directory {}\nFalling back to {}".format(
                            launcher_basedir, reg_basedir), "Error while setting launcher directory")
                self.set_launcher_basedir(reg_basedir)

        if not os.path.isdir(launcher_moddir):
            Logger.info('Settings: Creating mod dir - {}'.format(launcher_moddir))
            try:
                os.mkdir(launcher_moddir)
            except OSError:
                reg_moddir = self._get_launcher_basedir_from_reg()
                # TODO: Show a regular message box, not a win32 message box
                MessageBox("Could not create directory {}\nFalling back to {}".format(
                            launcher_moddir, reg_moddir), "Error while setting mod directory")
                self.set_launcher_moddir(reg_moddir)

        Logger.info("Settings: Launcher will use basedir: " + self.get_launcher_basedir())
        Logger.info("Settings: Launcher will use moddir: " + self.get_launcher_moddir())

    def _get_launcher_basedir_from_reg(self):
        """retreive users document folder from the registry"""
        user_docs = Registry.ReadValueCurrentUser(Settings._USER_DOCUMENT_PATH, 'Personal')
        path = os.path.join(user_docs, Settings._LAUNCHER_DIR)

        return path

    def get_launcher_basedir(self):
        return self.launcher_config.get('launcher_basedir')

    def set_launcher_basedir(self, value):
        return self.launcher_config.set('launcher_basedir', value)

    def get_launcher_moddir(self):
        moddir = self.launcher_config.get('launcher_moddir')
        if not moddir:
            moddir = os.path.join(self.get_launcher_basedir(), 'mods')

        return moddir

    def set_launcher_moddir(self, value):
        return self.launcher_config.set('launcher_moddir', value)

    def parse_args(self, argv):
        self.parser = argparse.ArgumentParser()

        self.parser.add_argument("-s", "--self-update",
                                 help="run the self updater",
                                 action="store_true")

        self.parser.add_argument("-d", "--launcher-basedir",
                                 help="specify the basedir for the launcher")

        settings_data = self.parser.parse_args(argv)

        for f in self.launcher_config.fields:
            value  = getattr(settings_data, f['name'], None)
            if value != None:
                self.launcher_config.set(f['name'], value)

    def get(self, key):
        """proxy method to the underlying LauncherConfig model"""
        return self.launcher_config.get(key)

    def set(self, key, value):
        """proxy method to the underlying LauncherConfig model"""
        self.launcher_config.set(key, value)
