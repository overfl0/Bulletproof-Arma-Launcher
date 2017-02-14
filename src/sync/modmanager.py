# Bulletproof Arma Launcher
# Copyright (C) 2016 Sascha Ebert
# Copyright (C) 2017 Lukasz Taczuk
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

import third_party

from manager_functions import (
    _get_mod_descriptions,
    _prepare_and_check,
    _sync_all,
)

from preparer import prepare_all

from kivy.logger import Logger
from utils.process import protected_para
from sync import torrent_uploader


class ModManager(object):
    """docstring for ModManager"""
    def __init__(self, settings):
        super(ModManager, self).__init__()
        self.settings = settings
        self.reset()

    def reset(self):
        self.clear_mods()
        self.clear_launcher()
        self.clear_servers()
        self.default_teamspeak_url = None

    def get_mods(self):
        return self.mods

    def clear_mods(self):
        self.mods = []

    def get_launcher(self):
        return self.launcher

    def clear_launcher(self):
        self.launcher = None

    def get_servers(self):
        return self.servers

    def clear_servers(self):
        self.servers = []

    def select_server(self, selection):
        if selection is None:
            self.settings.set('selected_server', selection)
            print 'Selected {}'.format(selection)

        for server in self.servers:
            if server['name'] == selection:
                self.settings.set('selected_server', selection)
                print 'Selected {}'.format(selection)

        return KeyError('Unknown server: {}'.format(selection))

    def _sanitize_server_list(self, servers, default_teamspeak):
        """Filter out only the servers that contain a 'name', 'ip' and 'port' fields."""

        checked_servers = servers[:]
        '''extra_server_string = devmode.get_extra_server()

        if extra_server_string:
            extra_server = {k: v for (k, v) in zip(('name', 'ip', 'port'), extra_server_string.split(':'))}
            checked_servers.insert(0, extra_server)
        '''

        ret_servers = filter(lambda x: all((x.get('name'), x.get('ip'), x.get('port'))), checked_servers)

        # Add the default values, if not provided
        for ret_server in ret_servers:
            ret_server.setdefault('teamspeak', default_teamspeak)
            ret_server.setdefault('password', None)
            ret_server.setdefault('mods', [])

        return ret_servers

    def run_the_game(self):
        selected_server = self.settings.get('selected_server')
        print 'Running connection to server: {}'.format(selected_server)
        # third_party.helpers.run_the_game(self.mod_manager.get_mods(), ip=ip, port=port, password=password, teamspeak_url=teamspeak_url)
        '''
        ip = port = password = None

        if self.servers:
            ip = self.servers[0]['ip']
            port = self.servers[0]['port']
            password = self.servers[0]['password']
            teamspeak_url = self.servers[0]['teamspeak']

        self.run_the_game(ip=ip, port=port, password=password, teamspeak_url=teamspeak_url)
        '''

    # Para functions below #####################################################

    def download_mod_description(self):
        para = protected_para(_get_mod_descriptions, (), 'download_description',
                              then=(self.on_download_mod_description_resolve,
                                    self.on_download_mod_description_reject,
                                    None)
                              )
        return para

    def on_download_mod_description_resolve(self, data):
        mod_description_data = data['data']
        self.settings.set('mod_data_cache', mod_description_data)

        self.default_teamspeak_url = mod_description_data.get('teamspeak', None)
        self.servers = self._sanitize_server_list(mod_description_data.get('servers', []), default_teamspeak=self.default_teamspeak_url)


    def on_download_mod_description_reject(self, data):
        self.reset()

        mod_data = self.settings.get('mod_data_cache')
        if not mod_data:
            return

        self.default_teamspeak_url = mod_data.get('teamspeak', None)
        self.servers = self._sanitize_server_list(mod_data.get('servers', []), default_teamspeak=self.default_teamspeak_url)

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

    def on_prepare_and_check_resolve(self, data):
        Logger.info('ModManager: Got mods ' + repr(data['mods']))
        self.mods = data['mods']
        self.launcher = data['launcher']

    def sync_all(self, seed):
        synced_elements = self.mods[:]  # Work on the copy
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

    def on_sync_all_progress(self, data, progress):
        Logger.debug('ModManager: Sync progress ' + repr(data))
        # Todo: modlist could be a class of its own

        mod_synchronised = data.get('workaround_finished')
        if mod_synchronised:
            for mod in self.mods:
                if mod.foldername == mod_synchronised:
                    mod.force_completion()

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
        para = protected_para(
            prepare_all,
            (list(self.mods), self.settings.get('launcher_moddir')),
            'prepare_all')
        return para

    def make_torrent(self, mods):
        para = protected_para(
            torrent_uploader.make_torrent,
            (
                self.settings.get('launcher_basedir'),
                mods
            ),
            'make_torrent'
        )
        return para


if __name__ == '__main__':
    pass
