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
import third_party.steam_query

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

    def get_mods(self, only_selected=False, include_base=True,
                 include_server=True, include_all_servers=False):
        if include_base:
            mods = self.mods[:]
        else:
            mods = []

        if include_all_servers:
            for server in self.servers:
                mods.extend(server.mods)

        elif include_server:
            server = self.get_selected_server()
            if server:
                mods.extend(server.mods)

        if only_selected:
            mods = filter(lambda x: not x.optional or x.selected, mods)

        return mods

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

    def get_selected_server(self):
        server_name = self.settings.get('selected_server')
        if server_name is None:
            return None

        if server_name is False:  # First time launcher user
            raise Exception('Self protection: can\'t get selected server. Selection is "False". Report this bug!')

        for server in self.servers:
            if server.name == server_name:
                return server

        raise KeyError('Selected server not present in servers list: {}'.format(server_name))

    def select_server(self, selection):
        if not self.servers:
            raise Exception('Self protection: can\'t select server if the server list is empty!')

        if selection is False:  # First time launcher user
            raise Exception('Self protection: can\'t select server. Selection is "False". Report this bug!')

        if selection is None:
            self.settings.set('selected_server', selection)
            Logger.info('select_server: Selected {}'.format(selection))
            return

        for server in self.servers:
            if server.name == selection:
                server.selected = True
                self.settings.set('selected_server', selection)
                Logger.info('select_server: Selected {}'.format(selection))
                return

            else:
                server.selected = False

        raise KeyError('Unknown server: {}'.format(selection))

    def select_first_server_available(self):
        """Select the first server from the server list.
        This function assumes the server list is not empty!

        return the selected server name
        """
        first_server_name = self.servers[0].name
        self.select_server(first_server_name)

        return first_server_name

    def run_the_game(self):
        server = self.get_selected_server()
        teamspeak = self.teamspeak
        battleye = self.battleye
        mods = self.get_mods(only_selected=True)

        Logger.info('run_the_game: Running Arma 3 and connecting to server: {}'.format(server))

        if server:
            if server.teamspeak:
                teamspeak = server.teamspeak
            if server.battleye is not None:
                battleye = server.battleye

            third_party.helpers.run_the_game(mods,
                                             ip=server.ip,
                                             port=server.port,
                                             password=server.password,
                                             teamspeak_urls=teamspeak,
                                             battleye=battleye)
        else:
            third_party.helpers.run_the_game(mods,
                                             ip=None,
                                             port=None,
                                             password=None,
                                             teamspeak_urls=teamspeak)

    # Para functions below #####################################################

    def download_mod_description(self, dry_run=False):
        if dry_run:
            then = None

        else:
            then = (self.on_download_mod_description_resolve,
                    self.on_download_mod_description_reject,
                    None)

        para = protected_para(_get_mod_descriptions,
                              (
                                  self.settings.get('auth_login'),
                                  self.settings.get('auth_password'),
                              ),
                              'download_description',
                              then=then
                              )
        return para

    def on_download_mod_description_resolve(self, data):
        self.settings.set('mod_data_cache', data['data'])

    def on_download_mod_description_reject(self, data):
        self.reset()

    def prepare_and_check(self, data):
        para = protected_para(
            _prepare_and_check,
            (
                self.settings.get('launcher_moddir'),
                self.settings.get('launcher_basedir'),
                data,
                self.settings.get('selected_optional_mods')
            ),
            'checkmods',
            then=(self.on_prepare_and_check_resolve, None, None)
        )

        return para

    def on_prepare_and_check_resolve(self, data):
        self.mods = data['mods']
        self.launcher = data['launcher']
        self.servers = data['servers']
        self.teamspeak = data['teamspeak']
        self.battleye = data['battleye']

        Logger.info('ModManager: Got base mods:\n' + '\n'.join(repr(mod)for mod in self.mods))
        Logger.info('ModManager: Got servers:\n' + '\n'.join(repr(server) for server in self.servers))

        if self.launcher:
            Logger.info('ModManager: Got launcher:\n{}'.format(repr(self.launcher)))

        if self.teamspeak:
            Logger.info('ModManager: Got base teamspeak:\n{}'.format(repr(self.teamspeak)))

        if self.battleye is not None:
            Logger.info('ModManager: Got base battleye:\n{}'.format(repr(self.battleye)))

    def sync_all(self, seed):
        synced_elements = self.get_mods(only_selected=True)  # Work on the copy
        if self.launcher:
            synced_elements.append(self.launcher)

        # If we are only seeding, ensure we pass only ready-to-seed mods
        # Note: the libtorrent seed-only flags prevent downloading data, but
        # still truncate the file anyway - something we want to prevent here
        if seed:
            synced_elements = filter(lambda mod: mod.is_complete(), synced_elements)

        para = protected_para(
            _sync_all,
            (
                synced_elements,
                self.settings.get('max_download_speed'),
                self.settings.get('max_upload_speed'),
                seed
            ),
            'sync',
            then=(None, None, self.on_sync_all_progress),
            use_threads=False
        )

        return para

    def on_sync_all_progress(self, data, progress):
        Logger.debug('ModManager: Sync progress ' + repr(data))
        # Todo: modlist could be a class of its own

        mod_synchronised = data.get('workaround_finished')
        if mod_synchronised:
            for mod in self.get_mods():
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
            then=(None, None, self.on_sync_all_progress),
            use_threads=False
        )

        return para

    def prepare_all(self):
        para = protected_para(
            prepare_all,
            # Note: the launcher takes the list of all the mod here but then it
            # drops the ones that are optional and not selected after the
            # directory normalizing process is done and before starting the
            # "search on disk for the mod" part.
            (self.get_mods(), self.get_mods(include_all_servers=True), self.settings.get('launcher_moddir')),
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

    @staticmethod
    def query_servers(servers):
        para = protected_para(
            third_party.steam_query.query_servers,
            (
                servers
            ),
            'query_servers'
        )
        return para


if __name__ == '__main__':
    pass
