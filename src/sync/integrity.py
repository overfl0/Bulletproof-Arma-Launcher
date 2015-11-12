# Tactical Battlefield Installer/Updater/Launcher
# Copyright (C) 2015 TacBF Installer Team.
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

import itertools
import os
import shutil

from arma.arma import Arma, ArmaNotInstalled
from contextlib import contextmanager
from utils.metadatafile import MetadataFile

def _unlink_safety_assert(base_path, file_path, action="remove"):
    """Asserts that the file_path string starts with base_path string.
    If this is not true then raise an exception"""

    real_base_path = os.path.realpath(base_path)
    real_file_path = os.path.realpath(file_path)
    if not real_file_path.startswith(real_base_path):
        message = "Something fishy is happening. Attempted to {} {} which is not inside {}!".format(
            action, real_file_path, real_base_path)
        raise Exception(message)


def _safer_unlink(base_path, file_path):
    """Checks if the base_path contains the file_path and removes file_path if true"""

    _unlink_safety_assert(base_path, file_path)
    os.unlink(file_path)


def _safer_rmtree(base_path, directory_path):
    """Checks if the base_path contains the directory_path and removes directory_path if true"""

    _unlink_safety_assert(base_path, directory_path)
    shutil.rmtree(directory_path)


def _raiser(exception):  # I'm sure there must be some builtin to do this :-/
    raise exception


@contextmanager
def _ignore_exceptions(*exceptions):
    try:
        yield
    except exceptions:
        pass


def filter_out_whitelisted(elements, whitelist):
    for whitelist_element in whitelist:
        file_match = os.path.sep + whitelist_element
        dir_match = os.path.sep + whitelist_element + os.path.sep
        elements = set(itertools.ifilterfalse(lambda x: x.endswith(file_match) or dir_match in x, elements))

    return elements

def check_mod_directories((top_dirs, dirs_orig, file_paths_orig), base_directory, check_subdir="", on_superfluous='warn'):
    """Check if all files and directories present in the mod directories belong
    to the torrent file. If not, remove those if on_superfluous=='remove' or return False
    if on_superfluous=='warn'.

    base_directory is the directory to which mods are downloaded.
    For example: if the mod directory is C:\Arma\@MyMod, base_directory should be C:\Arma.

    on_superfluous is the action to perform when superfluous files are found:
        'warn': return False
        'remove': remove the file or directory
        'ignore': do nothing

    To prevent accidental file removal, this function will only remove files
    that are at least one directory deep in the file structure!
    As all multi-file torrents *require* one root directory that holds those
    files, this should not be an issue.
    This function will skip files or directories that match the 'whitelist' variable.

    Returns if the directory has been cleaned sucessfully or if all files present
    are supposed to be there. Do not ignore this value!
    If unsuccessful at removing files, the mod should NOT be considered ready to play."""

    if not on_superfluous in ('warn', 'remove', 'ignore'):
        raise Exception('Unknown action: {}'.format(on_superfluous))

    dirs = dirs_orig.copy()
    file_paths = file_paths_orig.copy()

    # Whitelist our and PWS metadata files
    whitelist = (MetadataFile.file_name, '.synqinfo', '.sync')

    # Remove whitelisted items from the lists
    dirs = filter_out_whitelisted(dirs, whitelist)
    file_paths = filter_out_whitelisted(file_paths, whitelist)

    base_directory = os.path.realpath(base_directory)
    print "Cleaning up base_directory:", base_directory
    success = True

    try:
        for directory in top_dirs:
            with _ignore_exceptions(KeyError):
                dirs.remove(directory)

            if directory in whitelist:
                continue

            full_base_path = os.path.join(base_directory, directory)
            _unlink_safety_assert(base_directory, full_base_path, action='enter')
            for (dirpath, dirnames, filenames) in os.walk(full_base_path, topdown=True, onerror=_raiser, followlinks=False):
                relative_path = os.path.relpath(dirpath, base_directory)
                print 'In directory: {}'.format(relative_path)

                # First check files in this directory
                for file_name in filenames:
                    relative_file_name = os.path.join(check_subdir, relative_path, file_name)

                    if file_name in whitelist:
                        print 'File {} in whitelist, skipping...'.format(file_name)

                        with _ignore_exceptions(KeyError):
                            file_paths.remove(relative_file_name)
                        continue

                    print 'Checking file: {}'.format(relative_file_name)
                    if relative_file_name in file_paths:
                        file_paths.remove(relative_file_name)
                        print relative_file_name, "removed"
                        continue  # File present in the torrent, nothing to see here

                    full_file_path = os.path.join(dirpath, file_name)

                    if on_superfluous == 'remove':
                        print 'Removing file: {}'.format(full_file_path)
                        _safer_unlink(full_base_path, full_file_path)

                    elif on_superfluous == 'warn':
                        print 'Superfluous file: {}'.format(full_file_path)
                        return False

                    elif on_superfluous == 'ignore':
                        pass

                # Now check directories
                # Iterate over a copy because we'll be deleting items from the original
                for dir_name in dirnames[:]:
                    relative_dir_path = os.path.join(check_subdir, relative_path, dir_name)

                    if dir_name in whitelist:
                        dirnames.remove(dir_name)

                        with _ignore_exceptions(KeyError):
                            dirs.remove(relative_dir_path)

                        continue

                    print 'Checking dir: {}'.format(relative_dir_path)
                    if relative_dir_path in dirs:
                        dirs.remove(relative_dir_path)
                        continue  # Directory present in the torrent, nothing to see here

                    full_directory_path = os.path.join(dirpath, dir_name)

                    if on_superfluous == 'remove':
                        print 'Removing directory: {}'.format(full_directory_path)
                        dirnames.remove(dir_name)

                        _safer_rmtree(full_base_path, full_directory_path)

                    elif on_superfluous == 'warn':
                        print 'Superfluous directory: {}'.format(full_directory_path)
                        return False

                    elif on_superfluous == 'ignore':
                        pass

        # Check for files missing on disk
        if file_paths:
            success = False

        if dirs:
            success = False

    except OSError:
        success = False

    return success


def parse_files_list(files_list):
    """Computes the top directories, directories and the file paths contained in a torrent."""

    file_paths = set()
    dirs = set()
    top_dirs = set()

    for torrent_file in files_list:
        file_paths.add(torrent_file.path)
        dir_path = os.path.dirname(torrent_file.path)

        while dir_path:  # Go up the directory structure until the end
            if dir_path in dirs:  # If already processed for another file
                break

            dirs.add(dir_path)
            parent_dir = os.path.dirname(dir_path)
            if not parent_dir:
                top_dirs.add(dir_path)

            dir_path = parent_dir

    return (top_dirs, dirs, file_paths)


def check_files_mtime_correct(base_directory, files_data):  # file_path, size, mtime
    """Checks if all files have the right size and modification time.
    If the size or modification time differs, the file is considered modified
    and thus the check fails.

    Attention: The modification time check accuracy depends on a number of
    things such as the underlying File System type. Files are also allowed to be
    up to 5 minutes more recent than stated as per libtorrent implementation."""

    for file_path, size, mtime in files_data:
        try:
            full_file_path = os.path.join(base_directory, file_path)
            file_stat = os.stat(full_file_path)
        except OSError:
            print 'Could not perform stat on', full_file_path
            return False

        # print file_path, file_stat.st_mtime, mtime
        # Values for st_size and st_mtime based on libtorrent/src/storage.cpp: 135-190 // match_filesizes()
        if file_stat.st_size < size:  # Actually, not sure why < instead of != but kept this to be compatible with libtorrent
            print 'Incorrect file size for', full_file_path
            return False

        # Allow for 1 sec discrepancy due to FAT32
        # Also allow files to be up to 5 minutes more recent than stated
        if int(file_stat.st_mtime) > mtime + 5 * 60 or int(file_stat.st_mtime) < mtime - 1:
            print 'Incorrect modification time for', full_file_path
            return False

    return True


def is_complete_tfr_hack(mod_name, file_paths):
    """This is a hackish check if Task Force Arrowhead Radio mod has been
    correctly installed.
    To be fully installed, files contained in the userconfig subdirectory
    must be present in in Arma 3/userconfig directory. Additionally, a check
    if plugins have been copied to Teamspeak directory is made.
    """

    # If the checked mod is not TFR, happily return rainbows and unicorns
    if not mod_name.startswith("Task Force Arrowhead Radio"):
        return True

    try:
        arma_path = Arma.get_installation_path()
    except ArmaNotInstalled:
        # For testing purposes
        arma_path = "C:\\Users\\IEUser\\Documents\Arma 3"

    # Check if all files in userconfig are PRESENT (not necessarily the same)
    for entry in file_paths:
        # path == @task_force_radio\userconfig\...
        entry_pieces = os.path.normpath(entry).split(os.path.sep)
        if entry_pieces[1] == "userconfig":
            supposed_file_path = os.path.join(arma_path, *entry_pieces[1:])

            if not os.path.isfile(supposed_file_path):
                print "File {} not present. Marking as not fully installed".format(supposed_file_path)
                return False
            # print entry_path_rest

    # TODO: Check for the plugins in Teamspeak

    return True
