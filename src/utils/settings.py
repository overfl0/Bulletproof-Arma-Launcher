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
"""
Module to hold launcher specific model stuff
"""

from __future__ import unicode_literals

import argparse
import launcher_config
import os

from kivy.logger import Logger
from kivy.event import EventDispatcher
from third_party.arma import Arma, SoftwareNotInstalled
from utils.critical_messagebox import MessageBox
from utils.data.jsonstore import JsonStore
from utils.data.model import ModelInterceptorError, Model
from utils.paths import mkdir_p, get_launcher_directory

# str variant of the unicode string on_change
# kivy's api only works with non unicode strings
ON_CHANGE = b'on_change'


class Settings(Model):
    """
    Settings class is a manager and validation layer to the underlying
    model which can be used to save user preferences.


    This class defines get and set interceptors which should NOT Be
    called from the outside.

    Auto-saving:
        On default, the settings-model saves it self on change. To
        disable this behaviour, call suspend_autosave(). To re-enable
        the Auto-saving call resume_autosave()

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
        # Temporary values
        {'name': 'use_exception_popup', 'defaultValue': False, 'persist': False},
        {'name': 'update', 'defaultValue': False, 'persist': False},
        {'name': 'automatic_download', 'defaultValue': False, 'persist': False},
        {'name': 'automatic_seed', 'defaultValue': False, 'persist': False},

        # Other persisting
        {'name': 'basedir_change_notice', 'defaultValue': 0},
        {'name': 'launcher_basedir'},
        {'name': 'launcher_moddir'},
        {'name': 'mod_data_cache', 'defaultValue': None},
        {'name': 'max_upload_speed', 'defaultValue': 0},
        {'name': 'max_download_speed', 'defaultValue': 0},
        {'name': 'seeding_type', 'defaultValue': 'while_not_playing'},
        {'name': 'selected_server', 'defaultValue': False},
        {'name': 'run_trackir', 'defaultValue': True},
        {'name': 'run_opentrack', 'defaultValue': True},
        {'name': 'run_facetracknoir', 'defaultValue': True},
        {'name': 'selected_optional_mods', 'defaultValue': []},
        {'name': 'last_custom_background', 'defaultValue': None},
        {'name': 'auth_login', 'defaultValue': ''},
        {'name': 'auth_password', 'defaultValue': ''},

        # Arma launching parameters ############################################
        {'name': 'arma_win32', 'defaultValue': False},
        {'name': 'arma_win64', 'defaultValue': False},
        {'name': 'arma_name', 'defaultValue': ''},
        {'name': 'arma_name_enabled', 'defaultValue': False},
        {'name': 'arma_showScriptErrors', 'defaultValue': False},
        {'name': 'arma_noPause', 'defaultValue': True},
        {'name': 'arma_window', 'defaultValue': False},
        {'name': 'arma_checkSignatures', 'defaultValue': False},
        {'name': 'arma_filePatching', 'defaultValue': False},
        {'name': 'arma_unit', 'defaultValue': ''},
        {'name': 'arma_unit_enabled', 'defaultValue': False},
        {'name': 'arma_mission_file', 'defaultValue': ''},
        {'name': 'arma_mission_file_enabled', 'defaultValue': False},
        {'name': 'arma_exThreads', 'defaultValue': '0'},
        {'name': 'arma_exThreads_enabled', 'defaultValue': False},
        {'name': 'arma_noSound', 'defaultValue': False},
        {'name': 'arma_hugePages', 'defaultValue': False},
        {'name': 'arma_additionalParameters', 'defaultValue': ''},
    ]

    # path to the registry entry which holds the users document path
    _USER_DOCUMENT_PATH = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"

    def __init__(self, argv):
        super(Settings, self).__init__()
        # save automatically to disc if changes to the settings are made
        self.auto_save_on_change = True

        # get the basedir for config files. This has to be the same every time
        self.config_path = os.path.join(self.launcher_default_basedir(), 'config.json')

        # load config
        try:
            store = JsonStore(self.config_path)
            # this is ugly self modification, but i don't want to introduce
            # a settings manager
            store.load(self, update=True)
        except Exception:
            Logger.warn('Settings: Launcher config could not be loaded')

        # parse arguments
        self.parser = None
        self.parse_args(argv)

        Logger.info('Settings: loaded args: ' + unicode(self.data))

    @classmethod
    def launcher_default_basedir(cls):
        """Retrieve users document folder from the registry"""
        path = get_launcher_directory()

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
        If that fails, use "Arma 3/<launcher_config.default_mods_dir>" directory.
        If that also fails (because there is no Arma, for example) use basedir/mods.
        """
        try:
            if not moddir:
                moddir = os.path.join(Arma.get_installation_path(), launcher_config.default_mods_dir)
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

        self.parser.add_argument("-u", "--update", metavar='OLD_EXECUTABLE',
            help="Run the self updater. OLD_EXECUTABLE is the file to be updated.")

        self.parser.add_argument("-d", "--launcher-basedir",
                                 help="Specify the basedir for the launcher")

        self.parser.add_argument("-r", "--run-updated", action='store_true',
            help="Dummy switch to test autoupdate")

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
