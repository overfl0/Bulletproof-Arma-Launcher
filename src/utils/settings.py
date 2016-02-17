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
"""
Module to hold launcher specific model stuff
"""

from __future__ import unicode_literals

import argparse
import os

from kivy.logger import Logger
from kivy.event import EventDispatcher
from third_party.arma import Arma, SoftwareNotInstalled
from utils.critical_messagebox import MessageBox
from utils.data.jsonstore import JsonStore
from utils.data.model import ModelInterceptorError, Model
from utils.paths import mkdir_p
from utils.registry import Registry

# str variant of the unicode string on_change
# kivys api only works with non unicode strings
ON_CHANGE = 'on_change'.encode('ascii')


class Settings(Model):
    """
    Settings class is a manager and validation layer to the underlying
    model which can be used to save user preferences.

    This class defines get and set interceptors which should NOT Be
    called from the outside.

    Autosaving:
        On default, the settins-model saves it self on change. To
        disable this behaviour, call suspend_autosave(). To reenable
        the Autosaving call resume_autosave()

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
    fields = [
        {
            'name': 'use_exception_popup',
            'defaultValue': False,
            'persist': False
        }, {
            'name': 'self_update',
            'defaultValue': False,
            'persist': False
        }, {
            'name': 'launcher_basedir'
        }, {
            'name': 'launcher_moddir'
        }, {
            'name': 'mod_data_cache', 'defaultValue': None
        }, {
            'name': 'max_upload_speed', 'defaultValue': 0
        }, {
            'name': 'max_download_speed', 'defaultValue': 0
        }, {
            'name': 'seeding_type', 'defaultValue': 'never'
        }
    ]

    # path to the registry entry which holds the users document path
    _USER_DOCUMENT_PATH = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"

    # the folder name where everything gets store. This will get the last
    # part of the launcher_basedir
    _LAUNCHER_DIR = 'TacBF Launcher'

    def __init__(self, argv):
        super(Settings, self).__init__()
        # save automaticly to disc if changes to the settings are made
        self.auto_save_on_change = True

        # get the basedir for config files. This has to be the same everytime
        self.config_path = os.path.join(self.launcher_default_basedir(), 'config.json')

        # load config
        try:
            store = JsonStore(self.config_path)
            # this is ugly self modification, but i dont want to introduce
            # a settingsmanager
            store.load(self, update=True)
        except:
            Logger.warn('Settings: Launcher config could not be loaded')

        # parse arguments
        self.parser = None
        self.parse_args(argv)

        Logger.info('Settings: loaded args: ' + unicode(self.data))

    @classmethod
    def launcher_default_basedir(cls):
        """Retrieve users document folder from the registry"""
        user_docs = Registry.ReadValueCurrentUser(cls._USER_DOCUMENT_PATH, 'Personal')
        path = os.path.join(user_docs, cls._LAUNCHER_DIR)

        return path

    def _get_launcher_basedir(self, basedir):
        """interceptor which returnbs the launcher default basedir,
        if the basedir was not user set"""
        if not basedir:
            return self.launcher_default_basedir()
        else:
            return basedir

    def _set_launcher_basedir(self, launcher_basedir):
        """
        interceptor for launcher_basedir
        sets the user defined launcher_basedir and ensures it is created. If
        something goes wrong nothing is done
        """
        Logger.info('Settings: Ensuring basedir exists - {}'.format(launcher_basedir))
        try:
            mkdir_p(launcher_basedir)
        except OSError:
            # TODO: Show a regular message box, not a win32 message box
            MessageBox('Could not create directory {}\n Setting will stay on {}'.format(
                launcher_basedir, self.get('launcher_basedir')),
                'Error while setting launcher directory')
            return ModelInterceptorError()

        return launcher_basedir

    def _get_launcher_moddir(self, moddir):
        """
        interceptor for launcher_moddir
        Try to get the mod directory from the settings.
        If that fails, use "Arma 3/Tactical Battlefield" directory.
        If that also fails (because there is no Arma, for example) use basedir/mods.
        """
        try:
            if not moddir:
                moddir = os.path.join(Arma.get_installation_path(), 'Tactical Battlefield')
        except SoftwareNotInstalled:
            pass

        if not moddir:
            moddir = os.path.join(self.get('launcher_basedir'), 'mods')

        return moddir

    def _set_launcher_moddir(self, launcher_moddir):
        """
        interceptor for launcher_moddir
        sets the user defined launcher_moddir and ensures it is created. If
        something goes wrong nothing is done
        """
        Logger.info('Settings: Ensuring mod dir exists - {}'.format(launcher_moddir))
        try:
            mkdir_p(launcher_moddir)
        except OSError:
            fallback_moddir = self.get('launcher_moddir')
            # TODO: Show a regular message box, not a win32 message box
            MessageBox('Could not create directory {}\nFalling back to {}'.format(
                launcher_moddir, fallback_moddir), 'Error while setting mod directory')
            return ModelInterceptorError()

        return launcher_moddir

    def suspend_autosave(self):
        """disables the auto save mechanic of the model"""
        self.auto_save_on_change = False

    def resume_autosave(self):
        """enables the auto save mechanic of the model"""
        self.auto_save_on_change = True

    def parse_args(self, argv):
        """parse arguments from the commandline and write them into the model"""
        self.parser = argparse.ArgumentParser()

        self.parser.add_argument("-s", "--self-update",
                                 help="run the self updater",
                                 action="store_true")

        self.parser.add_argument("-d", "--launcher-basedir",
                                 help="specify the basedir for the launcher")

        settings_data = self.parser.parse_args(argv)

        self.suspend_autosave()
        for field in self.fields:
            value = getattr(settings_data, field['name'], None)
            if value is not None:
                self.set(field['name'], value)
        self.resume_autosave()

    def on_change(self, key, old_value, new_value):
        """
        overwrite on_change method of Model
        """
        Logger.debug(
            'Settings: settings changed. New value for key "{}" is: {}'.format(key, new_value))

        if self.auto_save_on_change:
            Logger.debug('Settings: saving config to: {}'.format(self.config_path))
            store = JsonStore(self.config_path)
            store.save(self)
