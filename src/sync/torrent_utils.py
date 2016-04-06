# Tactical Battlefield Installer/Updater/Launcher
# Copyright (C) 2016 TacBF Installer Team.
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
import libtorrent
import os
import stat

from kivy.logger import Logger
from sync.integrity import check_mod_directories, check_files_mtime_correct, is_complete_tfr_hack
from utils.metadatafile import MetadataFile
from utils import unicode_helpers


class AdminRequiredError(Exception):
    pass


def is_complete_quick(mod):
    """Performs a quick check to see if the mod *seems* to be correctly installed.
    This check assumes no external changes have been made to the mods.

    1. Check if metadata file exists and can be opened (instant)
    2. Check if torrent is not dirty [download completed successfully] (instant)
    3. Check if torrent url matches (instant)
    4. Check if files have the right size and modification time (very quick)
    5. Check if there are no superfluous files in the directory (very quick)"""

    metadata_file = MetadataFile(mod.foldername)

    # (1) Check if metadata can be opened
    try:
        metadata_file.read_data(ignore_open_errors=False)
    except IOError:
        Logger.info('Metadata file could not be read successfully. Marking as not complete')
        return False

    # (2)
    if metadata_file.get_dirty():
        Logger.info('Torrent marked as dirty (not completed successfully). Marking as not complete')
        return False

    # (3)
    if metadata_file.get_torrent_url() != mod.downloadurl:
        Logger.info('Torrent urls differ. Marking as not complete')
        return False

    # Get data required for (4) and (5)
    torrent_content = metadata_file.get_torrent_content()
    if not torrent_content:
        Logger.info('Could not get torrent file content. Marking as not complete')
        return False

    try:
        torrent_info = get_torrent_info_from_bytestring(torrent_content)
    except RuntimeError:
        Logger.info('Could not parse torrent file content. Marking as not complete')
        return False

    resume_data_bencoded = metadata_file.get_torrent_resume_data()
    if not resume_data_bencoded:
        Logger.info('Could not get resume data. Marking as not complete')
        return False
    resume_data = libtorrent.bdecode(resume_data_bencoded)

    # (4)
    file_sizes = resume_data['file sizes']
    files = torrent_info.files()
    # file_path, size, mtime
    files_data = map(lambda x, y: (y.path.decode('utf-8'), x[0], x[1]), file_sizes, files)

    if not check_files_mtime_correct(mod.clientlocation, files_data):
        Logger.info('Some files seem to have been modified in the meantime. Marking as not complete')
        return False

    # (5) Check if there are no additional files in the directory
    checksums = dict([(entry.path.decode('utf-8'), entry.filehash.to_bytes()) for entry in torrent_info.files()])
    files_list = checksums.keys()
    if not check_mod_directories(files_list, mod.clientlocation, on_superfluous='warn'):
        Logger.info('Superfluous files in mod directory. Marking as not complete')
        return False

    return is_complete_tfr_hack(mod.name, files_list, checksums)


def get_torrent_info_from_bytestring(bencoded):
    """Get torrent metadata from a bencoded string and return info structure."""

    torrent_metadata = libtorrent.bdecode(bencoded)
    torrent_info = libtorrent.torrent_info(torrent_metadata)

    return torrent_info


def get_torrent_info_from_file(filename):
    """Get torrent_info structure from a file.
    The file should contain a bencoded string - the contents of a .torrent file."""

    with open(filename, 'rb') as file_handle:
        file_contents = file_handle.read()

        return get_torrent_info_from_bytestring(file_contents)


def ensure_files_are_read_write(base_directory, files_list, mod_foldername):
    """Ensures all the files have the write bit set. Useful if some external
    has set them to read-only.
    """

    mod_directory = os.path.join(base_directory, mod_foldername)
    Logger.info('Torrent_utils: Checking read-write file access in directory: {}.'.format(mod_directory))
    for torrent_file in files_list:

        node_path = os.path.join(base_directory, torrent_file)
        fs_node_path = unicode_helpers.u_to_fs(node_path)

        try:
            stat_struct = os.lstat(fs_node_path)

        except OSError as e:
            if e.errno == errno.ENOENT:  # 2 - File not found
                continue

        # If the file is read-only to the owner, change it to read-write
        if not stat_struct.st_mode & stat.S_IWUSR:
            Logger.info('Integrity: Setting write bit to file: {}'.format(node_path))
            try:
                os.chmod(fs_node_path, stat_struct.st_mode | stat.S_IWUSR)

            except OSError as ex:
                if ex.errno == errno.EACCES:  # 13
                    error_message = 'Error: file {} is read-only and cannot be changed. Running the launcher as Administrator may help.'.format(node_path)
                    Logger.error(error_message)
                    raise AdminRequiredError(error_message)
                else:
                    raise


def create_add_torrent_flags():
    """Create default flags for adding a new torrent to a syncer."""
    f = libtorrent.add_torrent_params_flags_t

    flags = 0
    flags |= f.flag_apply_ip_filter  # default
    flags |= f.flag_update_subscribe  # default
    # flags |= f.flag_merge_resume_trackers  # default off
    # flags |= f.flag_paused
    flags |= f.flag_auto_managed
    flags |= f.flag_override_resume_data
    # flags |= f.flag_seed_mode
    # flags |= f.flag_upload_mode
    # flags |= f.flag_share_mode
    flags |= f.flag_duplicate_is_error  # default?

    # no_recheck_incomplete_resume

    return flags
