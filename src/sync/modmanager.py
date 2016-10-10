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

import kivy
import kivy.app  # To keep PyDev from complaining

from manager_functions import (
    _get_mod_descriptions,
    _make_torrent,
    _prepare_and_check,
    _sync_all,
)

from preparer import prepare_all

from kivy.logger import Logger
from utils.process import protected_para


class ModManager(object):
    """docstring for ModManager"""
    def __init__(self):
        super(ModManager, self).__init__()
        self.mods = []
        self.launcher = None
        self.settings = kivy.app.App.get_running_app().settings

    def download_mod_description(self):
        para = protected_para(_get_mod_descriptions, (), 'download_description')
        return para

    def make_torrent(self, mods):
        para = protected_para(
            _make_torrent,
            (
                self.settings.get('launcher_basedir'),
                mods
            ),
            'make_torrent'
        )
        return para

    def prepare_and_check(self, data):
        para = protected_para(
            _prepare_and_check,
            (
                self.settings.get('launcher_moddir'),
                self.settings.get('launcher_basedir'),
                data
            ),
            'checkmods',
            then=(self.on_prepare_and_check_resolve, None, None)
        )

        return para

    def sync_all(self, seed):
        synced_elements = list(self.mods)
        if self.launcher:
            synced_elements.append(self.launcher)

        para = protected_para(
            _sync_all,
            (
                synced_elements,
                self.settings.get('max_download_speed'),
                self.settings.get('max_upload_speed'),
                seed
            ),
            'sync',
            then=(None, None, self.on_sync_all_progress)
        )

        return para

    def sync_launcher(self, seed=False):
        para = protected_para(
            _sync_all,
            (
                [self.launcher],
                self.settings.get('max_download_speed'),
                self.settings.get('max_upload_speed'),
                seed
            ),
            'sync',
            then=(None, None, self.on_sync_all_progress)
        )

        return para

    def prepare_all(self):
        para = protected_para(prepare_all, (list(self.mods),), 'prepare_all')
        return para

    def on_prepare_and_check_resolve(self, data):
        Logger.info('ModManager: Got mods ' + repr(data['mods']))
        self.mods = data['mods']
        self.launcher = data['launcher']

    def on_sync_all_progress(self, data, progress):
        Logger.debug('ModManager: Sync progress ' + repr(data))
        # Todo: modlist could be a class of its own

        mod_synchronised = data.get('workaround_finished')
        if mod_synchronised:
            for mod in self.mods:
                if mod.foldername == mod_synchronised:
                    mod.up_to_date = True


if __name__ == '__main__':
    pass
