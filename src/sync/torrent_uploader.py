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

import errno
import inspect
import json
import launcher_config
import os
import textwrap
import time

from collections import OrderedDict
from kivy.logger import Logger
from kivy.config import Config
from manager_functions import _torrent_url_base
from sync import torrent_utils
from sync import manager_functions
from utils.devmode import devmode
from utils import pypeeker
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
    metadata_file = devmode.get_server_metadata_filename('metadata.json')
    torrents_path = devmode.get_server_torrents_path(mandatory=True)
    server_delay = devmode.get_server_torrent_delay(0)


# Note: this is using an experimental message passing method and should be moved
# to other places in the future


class Message(object):

    def __init__(self, message_type, name, msg, *args, **kwargs):
        super(Message, self).__init__(*args, **kwargs)

        self.type = message_type
        self.name = name
        self.msg = msg

        self.data = kwargs
        self.data['msg'] = msg
        self.data['name'] = name
        self.data['action'] = message_type

    @staticmethod
    def msgbox(msg, name):
        return Message(message_type='msgbox', msg=msg, name=name)


def make_torrent(message_queue, launcher_basedir, mods):
    """This is actually a message loop wrapper working on python coroutines."""

    value_generator = _make_torrent(message_queue, launcher_basedir, mods)
    if not inspect.isgenerator(value_generator):
        Logger.info('make_torrent: Not a generator, returning the value')
        return value_generator

    Logger.info('make_torrent: Received a generator, starting message loop')

    try:
        value_to_send = None

        # Loop while the generator generates requests
        while True:
            yielded = value_generator.send(value_to_send)
            value_to_send = None

            if yielded.type == 'msgbox':
                message_queue.progress(yielded.data, 0)

            # Loop until you receive the right reply message
            while True:
                message = message_queue.receive_message()
                if not message:
                    time.sleep(0.1)
                    continue

                command = message.get('command')
                params = message.get('params')

                Logger.debug('Got command: {}'.format(command))

                if command == 'terminate':
                    Logger.info('make_torrent: Received terminate command. Closing generator...')
                    value_generator.close()
                    return

                # Check if it's the message we're waiting for
                if command == yielded.name:
                    break

            value_to_send = params

    except StopIteration:
        Logger.info('make_torrent: generator terminated')


def _make_torrent(message_queue, launcher_basedir, mods):
    """Create torrents from mods on the disk."""

    Logger.info('make_torrent: Starting the torrents creations process...')
    # announces = ['http://{}/announce.php'.format(launcher_config.domain)]
    announces = devmode.get_torrent_tracker_urls()
    web_seeds = devmode.get_torrent_web_seeds()

    if web_seeds is None:
        web_seeds = []

    if not announces:
        Logger.error('make_torrent: torrent_tracker_urls cannot be empty!')
        message_queue.reject({'msg': 'torrent_tracker_urls cannot be empty!'})
        return

    mods_created = []

    counter = 0
    for mod in mods:
        counter += 1

        if mod.is_complete():
            Logger.info('make_torrent: Mod {} is up to date, skipping...'.format(mod.foldername))
            continue

        Logger.info('make_torrent: Generating new torrent for mod {}...'.format(mod.foldername))

        timestamp = manager_functions.create_timestamp(time.time())
        output_file = '{}-{}.torrent'.format(mod.foldername, timestamp)
        output_path = os.path.join(launcher_basedir, output_file)
        comment = '{} dependency on mod {}'.format(launcher_config.launcher_name, mod.foldername)

        directory = os.path.join(mod.parent_location, mod.foldername)
        if not os.path.exists(directory):
            Logger.error('make_torrent: Directory does not exist! Skipping. Directory: {}'.format(directory))
            continue

        message_queue.progress({'msg': 'Creating file: {}'.format(output_file)}, counter / len(mods))
        file_created = torrent_utils.create_torrent(directory, announces, output_path, comment, web_seeds)
        with file(file_created, 'rb') as f:
            mod.torrent_content = f.read()
        mod.torrent_url = '{}{}'.format(_torrent_url_base(), output_file)
        mods_created.append((mod, file_created, output_file, timestamp))
        Logger.info('make_torrent: New torrent for mod {} created!'.format(mod.foldername))

    if mods_created:
        mods_user_friendly_list = []
        for mod, _, _, _ in mods_created:
            if hasattr(mod, 'is_launcher'):
                mods_user_friendly_list.append('{} ({})'.format(
                    mod.foldername, get_new_launcher_version(mod)))
            else:
                mods_user_friendly_list.append(mod.foldername)

        message = textwrap.dedent('''
            The following mods have been prepared to be updated:

            {}

            Click OK to upload all those mods to the server.
            If you do not want to upload ALL those mods, close the launcher now.

            After the upload is done, the launcher will start seeding all the new mods.
            You CAN then start and stop the launcher as you wish as long as you
            enabled seeding in OPTIONS!

            Make sure the mods are fully uploaded before you stop seeding for good.
            ''').format('\n'.join(mods_user_friendly_list))

        yield Message.msgbox(message, name='confirm_upload_mods')
        perform_update(message_queue, mods_created)

        for mod, _, _, _ in mods_created:
            torrent_utils.set_torrent_complete(mod)

    message_queue.resolve({'msg': 'Torrents created: {}'.format(len(mods_created)),
                           'mods_created': len(mods_created)})


def get_new_launcher_version(mod):
    """Return the real version of the launcher, stored on disk and pointed to by
    mod.
    mod must be a launcher autoupdate mod.
    mod must be in a consistent state (fully working executable).
    """

    mod_base_path = mod.get_full_path()
    launcher_executable_path = os.path.join(mod_base_path, launcher_config.executable_name + '.exe')

    version = pypeeker.get_version(launcher_executable_path)
    return version


def update_metadata_json(metadata_json_orig, mods_created):
    """Modify the metadata_json given as input to use the updated mods.
    Return the modified metadata_json contents.
    """

    tree = json.loads(metadata_json_orig, object_pairs_hook=lambda x : OrderedDict(x))

    for mod, _, _, timestamp in mods_created:
        # Perform the global mods update
        for mod_leaf in tree.get('mods', []):
            if mod_leaf['foldername'] == mod.foldername:
                mod_leaf['torrent-timestamp'] = timestamp

        # Perform the launcher update
        if 'launcher' in tree:
            if tree['launcher']['foldername'] == mod.foldername:
                tree['launcher']['torrent-timestamp'] = timestamp

                # Get the new mod version
                tree['launcher']['version'] = get_new_launcher_version(mod)

        # Perform the per-server mods update
        # Note: update the hidden servers, if present
        for server in tree.get('servers', []) + tree.get('hidden_servers', []):
            for mod_leaf in server.get('mods', []):
                if mod_leaf['foldername'] == mod.foldername:
                    mod_leaf['torrent-timestamp'] = timestamp

    metadata_json_modified = json.dumps(tree, indent=4, separators=(',', ': '))
    return metadata_json_modified


def perform_update(message_queue, mods_created):
    """Connect to the remote server, remove old, unused torrents, push newly
    created torrents and update metadata.json to use them.
    """

    Logger.info('perform_update: Starting the torrents remote update process...')
    message_queue.progress({'msg': 'Connecting to the server...'}, 1)

    with remote.RemoteConection(host, username, password, port) as connection:

        # Fetch metadata.json
        message_queue.progress({'msg': 'Fetching metadata.json...'}, 1)

        metadata_json_path = remote.join(metadata_path, metadata_file)
        try:
            metadata_json = connection.read_file(metadata_json_path)
        except IOError as ex:
            if ex.errno != errno.ENOENT:
                raise

            message_queue.reject({
                'msg': 'Could not fetch file from the server:\n{}'.format(metadata_json_path)})

        Logger.info('perform_update: Got metadata.json:\n{}'.format(metadata_json))

        metadata_json_updated = update_metadata_json(metadata_json, mods_created)

        # Delete old torrents
        message_queue.progress({'msg': 'Deleting old torrents...'}, 1)
        Logger.info('perform_update: Deleting old torrents...')
        for mod, local_file_path, file_name, _ in mods_created:
            for remote_file_name in connection.list_files(torrents_path):
                if not remote_file_name.endswith('.torrent'):
                    continue

                if not remote_file_name.startswith(mod.foldername):
                    continue

                if len(remote_file_name) != len(file_name):
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
        for mod, local_file_path, file_name, _ in mods_created:
            remote_torrent_path = remote.join(torrents_path, file_name)
            connection.put_file(local_file_path, remote_torrent_path)

        message_queue.progress({'msg': 'Updating modified metadata.json...'}, 1)
        Logger.info('perform_update: Updated metadata.json:\n{}'.format(metadata_json_updated))

        # Push modified metadata.json
        connection.save_file(metadata_json_path, metadata_json_updated)

        message_queue.progress({'msg': 'Updating the mods is done!'}, 1)
