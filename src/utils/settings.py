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

import argparse
import os

from kivy.logger import Logger
from kivy.event import EventDispatcher
from third_party.arma import Arma, SoftwareNotInstalled
from utils.critical_messagebox import MessageBox
from utils.data.jsonstore import JsonStore
from utils.data.model import Model
from utils.paths import mkdir_p
from utils.registry import Registry

# str variant of the unicode string on_change
# kivys api only works with non unicode strings
ON_CHANGE = 'on_change'.encode('ascii')

class LauncherConfig(Model):
    """Container class for storing configuration"""

    fields = [
        {'name': 'use_exception_popup', 'defaultValue': False},
        {'name': 'self_update', 'defaultValue': False},
        {'name': 'launcher_basedir'},
        {'name': 'launcher_moddir'},
        {'name': 'mod_data_cache', 'defaultValue': None}
    ]

    def __init__(self):
        super(LauncherConfig, self).__init__()


class Settings(EventDispatcher):
    """
    Settings class is a manager and validation layer to the underlying
    LauncherConfig model which can be used to save user preferences.
    In any case it is recommended to use the set_* and get_* methods defined
    in this class in favour to setting values directly using the set method
    of the LauncherConfig class.

    For convinience, the Settings-Class proxies the set and get method of
    the underlying Model and refires the on_change event.

    Path definitions:
        launcher_default_basedir -> this path must be CONSTANT, is build up
            from the users document-root and the constant _LAUNCHER_DIR and is
            NOT saved to disc

        config_path -> launcher_default_basedir + "config.json"
            place where the config gets stored

        launcher_basedir -> can be set by user, and determines where stuff
            regarding the launcher gets stored

        launcher_moddir -> can be set by user, and determines where mods are
            stored

    """

    # save automaticly to disc if changes to the settings are made
    AUTO_SAVE_ON_CHANGE = True

    # path to the registry entry which holds the users document path
    _USER_DOCUMENT_PATH = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"

    # the folder name where everything gets store. This will get the last
    # part of the launcher_basedir
    _LAUNCHER_DIR = 'TacBF Launcher'

    def __init__(self, argv):
        super(Settings, self).__init__()

        # get the basedir for config files. This has to be the same everytime
        self.config_path = os.path.join(self._get_launcher_default_basedir(), 'config.json')

        # init LauncherConfig and bind to on change event
        self.launcher_config = LauncherConfig()
        self.launcher_config.bind(on_change=self.on_launcher_config_change)
        self.register_event_type(ON_CHANGE)

        # load config
        try:
            store = JsonStore(self.config_path)
            self.launcher_config = store.load(self.launcher_config, update=True)
        except:
            Logger.warn('Settings: Launcher config could not be loaded')

        # parse arguments
        self.parser = None
        self.parse_args(argv)

        Logger.info('Settings: loaded args: ' + unicode(self.launcher_config.data))

    def _get_launcher_default_basedir(self):
        """Retrieve users document folder from the registry"""
        user_docs = Registry.ReadValueCurrentUser(Settings._USER_DOCUMENT_PATH, 'Personal')
        path = os.path.join(user_docs, Settings._LAUNCHER_DIR)

        return path

    def get_launcher_basedir(self):
        basedir = self.launcher_config.get('launcher_basedir')
        if not basedir:
            basedir = self._get_launcher_default_basedir()

        return basedir

    def set_launcher_basedir(self, launcher_basedir):
        """
        sets the user defined launcher_basedir and ensures it is created. If
        something goes wrong nothing is done
        """
        Logger.info('Settings: Ensuring basedir exists - {}'.format(launcher_basedir))
        try:
            mkdir_p(launcher_basedir)
        except OSError:
            # TODO: Show a regular message box, not a win32 message box
            MessageBox('Could not create directory {}\n Setting will stay on {}'.format(
                        launcher_basedir, self.get_launcher_basedir()),
                    'Error while setting launcher directory')
            return self

        return self.launcher_config.set('launcher_basedir', launcher_basedir)

    def get_launcher_moddir(self):
        """Try to get the mod directory from the settings.
        If that fails, use "Arma 3\Tactical Battlefield" directory.
        If that also fails (because there is no Arma, for example) use basedir\mods.
        """

        moddir = self.launcher_config.get('launcher_moddir')
        try:
            if not moddir:
                moddir = os.path.join(Arma.get_installation_path(), 'Tactical Battlefield')
        except SoftwareNotInstalled:
            pass

        if not moddir:
            moddir = os.path.join(self.get_launcher_basedir(), 'mods')

        return moddir

    def set_launcher_moddir(self, launcher_moddir):
        """
        sets the user defined launcher_basedir and ensures it is created. If
        something goes wrong nothing is done
        """
        Logger.info('Settings: Ensuring mod dir exists - {}'.format(launcher_moddir))
        try:
            mkdir_p(launcher_moddir)
        except OSError:
            fallback_moddir = self.get_launcher_moddir()
            # TODO: Show a regular message box, not a win32 message box
            MessageBox('Could not create directory {}\nFalling back to {}'.format(
                       launcher_moddir, fallback_moddir), 'Error while setting mod directory')
            return self

        return self.launcher_config.set('launcher_moddir', launcher_moddir)

    def set_mod_data_cache(self, value):
        self.set('mod_data_cache', value)

    def get_mod_data_cache(self):
        return self.launcher_config.get('mod_data_cache')

    def parse_args(self, argv):
        self.parser = argparse.ArgumentParser()

        self.parser.add_argument("-s", "--self-update",
                                 help="run the self updater",
                                 action="store_true")

        self.parser.add_argument("-d", "--launcher-basedir",
                                 help="specify the basedir for the launcher")

        settings_data = self.parser.parse_args(argv)

        for f in self.launcher_config.fields:
            value = getattr(settings_data, f['name'], None)
            if value is not None:
                # TODO: suspend events here
                self.launcher_config.set(f['name'], value)

    def get(self, key):
        """proxy method to the underlying LauncherConfig model"""
        return self.launcher_config.get(key)

    def set(self, key, value):
        """proxy method to the underlying LauncherConfig model"""
        self.launcher_config.set(key, value)
        return self

    def on_change(self, key, old_value, new_value):
        Logger.debug('Settings: settings changed. New value is: {}'.format(new_value))

    def on_launcher_config_change(self, launcher_config, key, old_value, new_value):
        """refire the on_change event of the settings model"""
        self.dispatch(ON_CHANGE, key, old_value, new_value)
