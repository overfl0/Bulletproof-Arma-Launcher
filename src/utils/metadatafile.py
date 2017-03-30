# Bulletproof Arma Launcher
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

import base64
import errno
import json
import os

from kivy import Logger
from utils.paths import get_launcher_directory


class MetadataFile(object):
    """File that contains metadata about mods and is located in the root directory of each mod"""
    """TODO: Maybe screw the whole json part and just bencode everything?"""
    file_extension = '.launcher_meta'
    file_directory = 'mods_metadata'
    _encoding = 'utf-8'

    def __init__(self, mod_name):
        super(MetadataFile, self).__init__()

        file_name = '{}{}'.format(mod_name, self.file_extension)
        self.file_path = os.path.join(get_launcher_directory(), self.file_directory, file_name)
        self.data = {}

    def get_file_name(self):
        """Returns the full path to the metadata file"""
        return self.file_path

    def read_data(self, ignore_open_errors=False):
        """Open the file and read its data to an internal variable

        If ignore_open_errors is set to True, it will ignore errors while opening the file
        (which may not exist along with the whole directory if the torrent is downloaded for the first time)"""

        self.data = {}
        try:
            with open(self.get_file_name(), 'rb') as file_handle:
                self.data = json.load(file_handle, encoding=MetadataFile._encoding)
        except (IOError, ValueError):
            if ignore_open_errors:
                pass
            else:
                raise

    def _create_missing_directories(self, dirpath):
        """Creates missing directories. Does not raise exceptions if the path already exists

        Maybe move this to utils module in the future"""
        try:
            os.makedirs(dirpath)
        except OSError as exc:
            if exc.errno != errno.EEXIST or not os.path.isdir(dirpath):
                raise

    def write_data(self):
        """Open the file and write the contents of the internal data variable to the file"""
        self._create_missing_directories(os.path.dirname(self.get_file_name()))

        json_string = json.dumps(self.data, encoding=MetadataFile._encoding, indent=2)
        with open(self.get_file_name(), 'wb') as file_handle:
            file_handle.write(json_string)

    def set_base64_key(self, key_name, value):
        self.data[key_name] = base64.b64encode(value)

    def get_base64_key(self, key_name):
        data = self.data.setdefault(key_name, None)
        if data:
            try:
                data = base64.b64decode(data)
            except TypeError:
                data = None

        return data

    # Accessors and mutators below

    def set_torrent_url(self, url):
        self.data['torrent_url'] = url

    def get_torrent_url(self):
        return self.data.setdefault('torrent_url', '')

    def set_torrent_resume_data(self, data):
        self.set_base64_key('torrent_resume_data', data)

    def get_torrent_resume_data(self):
        return self.get_base64_key('torrent_resume_data')

    def set_torrent_content(self, torrent_content):
        self.set_base64_key('torrent_content', torrent_content)

    def get_torrent_content(self):
        return self.get_base64_key('torrent_content')

    def set_dirty(self, is_dirty):
        """Mark the torrent as dirty - in an inconsistent state (download started, we don't know what's exactly on disk)"""
        self.data['dirty'] = bool(is_dirty)
        Logger.info('set_dirty: Mod {}: {}'.format(self.get_file_name(), is_dirty))

    def get_dirty(self):
        return self.data.setdefault('dirty', False)

    def set_force_creator_complete(self, complete):
        self.data['force_creator_complete'] = complete

    def get_force_creator_complete(self):
        return self.data.setdefault('force_creator_complete', False)
