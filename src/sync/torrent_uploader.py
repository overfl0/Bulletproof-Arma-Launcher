# Bulletproof Arma Launcher
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

import os
import time

from config import config
from kivy.logger import Logger
from kivy.config import Config
from sync import torrent_utils
from sync import manager_functions
from utils.devmode import devmode
from utils import remote

default_log_level = devmode.get_log_level('info')
Config.set('kivy', 'log_level', default_log_level)

################################################################################
################################## ATTENTION!!! ################################
################################################################################
#
#
# Everything below this comment is run IN A DIFFERENT PROCESS!
# To communicate with the main program, you have to use the resolve(), reject()
# and progress() calls of the message queue!
#
#
################################################################################
################################## ATTENTION!!! ################################
################################################################################


if devmode.get_create_torrents():
    host = devmode.get_server_host(mandatory=True)
    username = devmode.get_server_username(mandatory=True)
    password = devmode.get_server_password(mandatory=True)
    port = devmode.get_server_port(22)
    metadata_path = devmode.get_server_metadata_path(mandatory=True)
    torrents_path = devmode.get_server_torrents_path(mandatory=True)


def make_torrent(message_queue, launcher_basedir, mods):
    """Create torrents from mods on the disk."""

    # announces = ['http://{}/announce.php'.format(config.domain)]
    announces = devmode.get_torrent_tracker_urls()
    web_seeds = devmode.get_torrent_web_seeds()

    if not announces:
        message_queue.reject({'msg': 'torrent_tracker_urls cannot be empty!'})
        return

    mods_created = []

    counter = 0
    for mod in mods:
        counter += 1

        if mod.up_to_date:
            continue

        output_file = '{}-{}.torrent'.format(mod.foldername, manager_functions.create_timestamp(time.time()))
        output_path = os.path.join(launcher_basedir, output_file)
        comment = '{} dependency on mod {}'.format(config.launcher_name, mod.foldername)

        directory = os.path.join(mod.parent_location, mod.foldername)
        if not os.path.exists(directory):
            continue

        message_queue.progress({'msg': 'Creating file: {}'.format(output_file)}, counter / len(mods))
        file_created = torrent_utils.create_torrent(directory, announces, output_path, comment, web_seeds)
        file_created_dir = os.path.dirname(file_created)

        mods_created.append((mod, file_created, output_file))

#     if files_created:
#         from utils import browser
#         browser.open_hyperlink(file_created_dir)

    if mods_created:
        perform_update(mods_created)

    message_queue.resolve({'msg': 'Torrents created: {}'.format(len(mods_created))})


def perform_update(mods_created):  # , new_mod_torrent_path):
    connection = remote.RemoteConection(host, username, password, port)
    connection.connect()

    try:
        metadata_json_path = remote.join(metadata_path, 'metadata.json')
        print metadata_json_path

        # Fetch metadata.json
        metadata_json = connection.read_file(metadata_json_path)
        # print metadata_json

        # Delete old torrents
        for mod, local_file_path, file_name in mods_created:
            for remote_file_name in connection.list_files(torrents_path):
                if not remote_file_name.endswith('.torrent'):
                    continue

                if not remote_file_name.startswith(mod.foldername):
                    continue

                # Got the file[s] to remove
                file_path = remote.join(torrents_path, remote_file_name)
                connection.remove_file(file_path)

        # Sleep custom amount of time
        if devmode.get_server_torrent_timeout(0):
            print "Sleeping"
            time.sleep(devmode.get_server_torrent_timeout(0))

        # Push new torrents
        for mod, local_file_path, file_name in mods_created:
            remote_torrent_path = remote.join(torrents_path, file_name)
            file_attributes = connection.put_file(local_file_path, remote_torrent_path)

        # Push modified metadata.json
        connection.save_file(metadata_json_path, metadata_json)

    finally:
        connection.close()
