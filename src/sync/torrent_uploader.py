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
    server_delay = devmode.get_server_torrent_delay(0)


def make_torrent(message_queue, launcher_basedir, mods):
    """Create torrents from mods on the disk."""

    Logger.info('make_torrent: Starting the torrents creations process...')
    # announces = ['http://{}/announce.php'.format(config.domain)]
    announces = devmode.get_torrent_tracker_urls()
    web_seeds = devmode.get_torrent_web_seeds()

    if not announces:
        Logger.error('make_torrent: torrent_tracker_urls cannot be empty!')
        message_queue.reject({'msg': 'torrent_tracker_urls cannot be empty!'})
        return

    mods_created = []

    counter = 0
    for mod in mods:
        counter += 1

        if mod.up_to_date:
            Logger.info('make_torrent: Mod {} is up to date, skipping...'.format(mod.foldername))
            continue

        Logger.info('make_torrent: Generating new torrent for mod {}...'.format(mod.foldername))

        output_file = '{}-{}.torrent'.format(mod.foldername, manager_functions.create_timestamp(time.time()))
        output_path = os.path.join(launcher_basedir, output_file)
        comment = '{} dependency on mod {}'.format(config.launcher_name, mod.foldername)

        directory = os.path.join(mod.parent_location, mod.foldername)
        if not os.path.exists(directory):
            Logger.error('make_torrent: Directory does not exist! Skipping. Directory: {}'.format(directory))
            continue

        message_queue.progress({'msg': 'Creating file: {}'.format(output_file)}, counter / len(mods))
        file_created = torrent_utils.create_torrent(directory, announces, output_path, comment, web_seeds)
        mods_created.append((mod, file_created, output_file))
        Logger.info('make_torrent: New torrent for mod {} created!'.format(mod.foldername))

    if mods_created:
        perform_update(message_queue, mods_created)

    message_queue.resolve({'msg': 'Torrents created: {}'.format(len(mods_created))})


def perform_update(message_queue, mods_created):
    Logger.info('perform_update: Starting the torrents remote update process...')
    message_queue.progress({'msg': 'Connecting to the server...'}, 1)

    with remote.RemoteConection(host, username, password, port) as connection:

        metadata_json_path = remote.join(metadata_path, 'metadata.json')
        print metadata_json_path

        # Fetch metadata.json
        metadata_json = connection.read_file(metadata_json_path)
        # print metadata_json

        # Delete old torrents
        message_queue.progress({'msg': 'Deleting old torrents...'}, 1)
        Logger.info('perform_update: Deleting old torrents...')
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
        if server_delay:
            message_queue.progress({'msg': 'Waiting {} seconds...'.format(server_delay)}, 1)
            Logger.info('perform_update: Sleeping {} seconds...'.format(server_delay))
            time.sleep(devmode.get_server_torrent_timeout(server_delay))

        # Push new torrents
        message_queue.progress({'msg': 'Pushing new torrents...'}, 1)
        Logger.info('perform_update: Pushing new torrents...')
        for mod, local_file_path, file_name in mods_created:
            remote_torrent_path = remote.join(torrents_path, file_name)
            connection.put_file(local_file_path, remote_torrent_path)

        # Push modified metadata.json
        message_queue.progress({'msg': 'Updating modified metadata.json...'}, 1)
        connection.save_file(metadata_json_path, metadata_json)

        message_queue.progress({'msg': 'Updating the mods is done!'}, 1)
