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

import shutil
import os
import time
import torrent_utils

from kivy.config import Config
from kivy.logger import Logger
from sync import finder
from utils.devmode import devmode


default_log_level = devmode.get_log_level('info')
Config.set('kivy', 'log_level', default_log_level)

# Everything in this file is run IN A DIFFERENT PROCESS!
# To communicate with the main program, you have to use the resolve(), reject()
# and progress() calls of the message queue!


class MessageHandler(object):
    def __init__(self, message_queue, owner):
        self.message_queue = message_queue
        self.owner = owner
        self.callbacks = {}

    def handle_messages(self):
        """Handle all incoming messages passed from the main process."""

        message = self.message_queue.receive_message()
        if not message:
            return

        command = message.get('command')
        params = message.get('params')

        try:
            callback = self.callbacks[command]
        except KeyError:
            Logger.error('MessageHandler: unknown command "{}" for object {}'.format(command, self.owner))

        if params is None:
            return callback()
        else:
            return callback(params)

    def send_message(self, command, params=None):
        """A wrapper around message_queue.progress to send messages."""

        data = {
            'special_message': {
                'command': command,
                'params': params
            }
        }
        self.message_queue.progress(data)

    def bind_message(self, command, callback):
        """Bind <callback> function to be called when <command> message arrives.
        Note: there can be only ONE callback assigned to a command at any time.
        """

        self.callbacks[command] = callback


class Preparer(object):
    def __init__(self, message_queue, mods, all_existing_mods, mods_directory):
        self.message_queue = message_queue
        self.mods = mods
        self.all_existing_mods = all_existing_mods
        self.mods_directory = mods_directory
        self.force_termination = False

        self.message_handler = MessageHandler(message_queue, self)
        self.message_handler.bind_message('terminate', self.on_terminate_message)
        self.message_handler.bind_message('mod_reuse', self.on_mod_reuse_message)
        self.message_handler.bind_message('mod_search', self.on_mod_search_message)

    def _get_mod_by_foldername(self, foldername):
        """Helper function to get the mod object by its foldername attribute."""

        for mod in self.mods:
            if mod.foldername == foldername:
                return mod

        raise KeyError('Could not find mod {}'.format(foldername))

    def on_terminate_message(self):
        """Terminate message has been received."""

        Logger.info('TorrentSyncer wants termination')
        self.force_termination = True

    def on_mod_reuse_message(self, params):
        """mod_reuse message has been received.
        If the argument is copy, copy the directory to the new location.
        If the argument is use, create a symlink (NTFS Junction currently).
        Decrease missing_responses.
        """

        self.missing_responses -= 1

        mod_name = params['mod_name']
        mod = self._get_mod_by_foldername(mod_name)

        if params['action'] == 'use':
            Logger.info('Message: Mod reuse: symlink, mod: {}'.format(mod_name))
            self.message_handler.message_queue.progress({'msg': 'Creating junction for mod {}...'.format(mod_name), 'log': []}, 0)
            torrent_utils.symlink_mod(mod.get_full_path(), params['location'])
            self.message_handler.message_queue.progress({'msg': 'Creating junction for mod {} finished!'.format(mod_name), 'log': []}, 0)

            self.missing_mods.remove(mod)

        elif params['action'] == 'copy':
            Logger.info('Message: Mod reuse: copy, mod: {}'.format(mod_name))
            self.message_handler.message_queue.progress({'msg': 'Copying mod {}...'.format(mod_name), 'log': []}, 0)
            shutil.copytree(params['location'], mod.get_full_path())
            torrent_utils.prepare_mod_directory(mod.get_full_path())
            self.message_handler.message_queue.progress({'msg': 'Copying mod {} finished!'.format(mod_name), 'log': []}, 0)

            self.missing_mods.remove(mod)

        elif params['action'] == 'discard':
            Logger.info('Message: Mod reuse: discard, mod: {}'.format(mod_name))
            self.missing_responses += 1  # Gratuitous message. Not waiting for it.

            try:
                self.missing_mods.remove(mod)
            except KeyError:
                pass  # May happen with discard when called twice

        elif params['action'] == 'ignore':
            # Kept here because we need to decrease the missing_responses count
            # and have a valid action that does just that.
            Logger.info('Message: Mod reuse: ignore, mod: {}'.format(mod_name))

        else:
            raise Exception('Unknown mod_reuse action: {}'.format(params['action']))

    def on_mod_search_message(self, params):
        """mod_search message has been received.
        The user has decided whether to search for mods in yet another
        directory or to just download all the remaining mods from the internet.
        """

        self.missing_responses -= 1

        if params['action'] == 'download':
            Logger.info('Message: Mod search: download all')
            self.missing_mods = set()  # Clear the missing mods

        elif params['action'] == 'search':
            Logger.info('Message: Mod search: search in {}'.format(params['location']))
            self.find_mods_and_ask([params['location']])

        else:
            raise Exception('Unknown mod_search action: {}'.format(params['action']))

    def reject(self, msg):
        """Wrapper around message_queue.reject."""

        self.message_queue.reject({'msg': msg})

    def find_mods_and_ask(self, locations=None):
        """Find all the potential mods located in <locations> and send the
        message to present the results to the user so they can make a choice.
        """
        self.message_queue.progress({'msg': 'Searching for missing mods on disk...',
                                    'log': [],
                                    }, 0)

        missing_mods_names = [mod.foldername for mod in self.missing_mods]
        # Find potential mods on disk.
        found_mods = finder.find_mods(self.mods_directory, missing_mods_names, self.all_existing_mods, locations)

        # For missing mods that have been found
        for mod_name in found_mods:
            self.message_handler.send_message('mod_found_action', {
                                                'mod_name': mod_name,
                                                'locations': found_mods[mod_name]
                                                })
            self.missing_responses += 1

    def request_directory_to_search(self):
        """Send a message with the list of missing mods to the main process."""

        mods_names = [mod.foldername for mod in self.missing_mods]
        self.message_handler.send_message('missing_mods', mods_names)
        self.missing_responses += 1

    def run(self):
        """First, ensure all mods directories that already exist are reachable
        and remove all those that are not (bad symlink).
        Then repeatedly ask the user to find missing mods until all mods are
        found or marked to be downloaded from the internet.
        """

        self.missing_mods = set()
        Logger.info('Preparer: Checking for missing mods.')

        try:
            for mod in self.mods:
                torrent_utils.prepare_mod_directory(mod.get_full_path())

            # Dropping all the mods that should not be shown here
            # (optional AND not selected)
            self.mods = filter(lambda m: not m.optional or m.selected, self.mods)

            for mod in self.mods:
                # If directory does not exist
                if not os.path.lexists(mod.get_full_path()):
                    self.missing_mods.add(mod)

        except torrent_utils.AdminRequiredError as ex:
            self.reject(ex.args[0])
            return

        self.missing_responses = 0

        if self.missing_mods:
            self.find_mods_and_ask()

        while self.missing_mods or self.missing_responses > 0:
            if not self.missing_responses:  # All responses have been processed
                # Print message about missing mods and ask for directory to search
                self.request_directory_to_search()

            self.message_handler.handle_messages()

            if self.force_termination:
                self.reject('Termination requested by parent')
                return

            time.sleep(0.1)

        # self.reject('Dummy reject message')
        self.message_queue.resolve()


def prepare_all(message_queue, mods, all_existing_mods, mods_directory):
    """Prepare all the mods' directories before downloading content.
    See preparer.run doc for more info.
    """

    preparer = Preparer(message_queue, mods, all_existing_mods, mods_directory)
    preparer.run()
