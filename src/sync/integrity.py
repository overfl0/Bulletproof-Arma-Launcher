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

# Allow relative imports when the script is run from the command line
if __name__ == "__main__":
    import site
    import os
    file_directory = os.path.dirname(os.path.realpath(__file__))
    site.addsitedir(os.path.abspath(os.path.join(file_directory, '..')))

import errno
import itertools
import os
import shutil

from kivy.logger import Logger
from utils import walker
from utils.context import ignore_exceptions
from utils.hashes import sha1
from utils.unicode_helpers import casefold
from third_party import teamspeak


# Whitelist special files
WHITELIST_NAME = ('tfr.ts3_plugin', '.synqinfo', '.sync')
WHITELIST_EXTENSION = ('.zsync',)

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
    """Checks if the base_path contains the directory_path and removes directory_path if true.
    Handles NTFS Junctions and Symlinks"""

    _unlink_safety_assert(base_path, directory_path)
    try:
        # Attempt to delete directory. Will work on empty directories,
        # NTFS junctions and NTFS symlinks (will delete the links instead of
        # the content).
        os.rmdir(directory_path)

    except OSError as ex:
        if ex.errno == errno.ENOTEMPTY:  # Not empty or not a Symlink/Junction
            shutil.rmtree(directory_path)

        else:
            raise


def _raiser(exception):  # I'm sure there must be some builtin to do this :-/
    raise exception


def is_whitelisted(node_path):
    """Check if the node full name or if its extension is whitelisted."""

    for whitelist_element in WHITELIST_NAME:
        if node_path.endswith(os.path.sep + whitelist_element):
            Logger.debug('is_whitelisted: Returning true for {}'.format(node_path))
            return True

    for whitelist_element in WHITELIST_EXTENSION:
        if node_path.endswith(whitelist_element):
            Logger.debug('is_whitelisted: Returning true for {}'.format(node_path))
            return True

    return False


def filter_out_whitelisted(elements):
    for whitelist_element in WHITELIST_NAME:
        file_match = os.path.sep + whitelist_element
        dir_match = os.path.sep + whitelist_element + os.path.sep
        elements = set(itertools.ifilterfalse(lambda x: x.endswith(file_match) or dir_match in x, elements))

    return elements


def check_mod_directories(files_list, base_directory, check_subdir='',
                          on_superfluous='warn', checksums=None,
                          case_sensitive=False):
    """Check if all files and directories present in the mod directories belong
    to the torrent file. If not, remove those if on_superfluous=='remove' or return False
    if on_superfluous=='warn'.

    base_directory is the directory to which mods are downloaded.
    For example: if the mod directory is C:\Arma\@MyMod, base_directory should be C:\Arma.

    check_subdir tells the function to only check if files contained in the
    subdirectory are properly created and existing.

    on_superfluous is the action to perform when superfluous files are found:
        'warn': return False
        'remove': remove the file or directory
        'ignore': do nothing

    To prevent accidental file removal, this function will only remove files
    that are at least one directory deep in the file structure!
    As all multi-file torrents *require* one root directory that holds those
    files, this should not be an issue.
    This function will skip files or directories that match the 'WHITELIST_NAME' variable.

    If the dictionary checksums is not None, the files' checksums will be checked.

    Returns if the directory has been cleaned sucessfully or if all files present
    are supposed to be there. Do not ignore this value!
    If unsuccessful at removing files, the mod should NOT be considered ready to play."""

    if on_superfluous not in ('warn', 'remove', 'ignore'):
        raise Exception('Unknown action: {}'.format(on_superfluous))

    top_dirs, dirs, file_paths, checksums = parse_files_list(files_list, checksums, check_subdir)

    # Remove whitelisted items from the lists
    dirs = filter_out_whitelisted(dirs)
    file_paths = filter_out_whitelisted(file_paths)

    # If not case sensitive, rewrite data so it may be used in a case insensitive
    # comparisons
    if not case_sensitive:
        file_paths = set(casefold(filename) for filename in file_paths)
        dirs = set(casefold(directory) for directory in dirs)
        top_dirs = set(casefold(top_dir) for top_dir in top_dirs)

        if checksums:
            checksums = {casefold(key): value for (key, value) in checksums.iteritems()}

        # Set conditional casefold function
        ccf = lambda x: casefold(x)
    else:
        ccf = lambda x: x

    base_directory = os.path.realpath(base_directory)
    Logger.debug('check_mod_directories: Verifying base_directory: {}'.format(base_directory))
    success = True

    try:
        for directory_nocase in top_dirs:
            with ignore_exceptions(KeyError):
                dirs.remove(directory_nocase)

            if directory_nocase in WHITELIST_NAME:
                continue

            full_base_path = os.path.join(base_directory, directory_nocase)
            _unlink_safety_assert(base_directory, full_base_path, action='enter')
            # FIXME: on OSError, this might indicate a broken junction or symlink on windows
            # Must act accordingly then.
            for (dirpath, dirnames, filenames) in walker.walk(full_base_path, topdown=True, onerror=_raiser, followlinks=True):
                relative_path = os.path.relpath(dirpath, base_directory)
                Logger.debug('check_mod_directories: In directory: {}'.format(relative_path))

                # First check files in this directory
                for file_name in filenames:
                    relative_file_name_nocase = ccf(os.path.join(relative_path, file_name))

                    if file_name in WHITELIST_NAME:
                        Logger.debug('check_mod_directories: File {} in WHITELIST_NAME, skipping...'.format(file_name))

                        with ignore_exceptions(KeyError):
                            file_paths.remove(relative_file_name_nocase)
                        continue

                    full_file_path = os.path.join(dirpath, file_name)

                    Logger.debug('check_mod_directories: Checking file: {}'.format(relative_file_name_nocase))
                    if relative_file_name_nocase in file_paths:
                        file_paths.remove(relative_file_name_nocase)
                        Logger.debug('check_mod_directories: {} present in torrent metadata'.format(relative_file_name_nocase))

                        if checksums and sha1(full_file_path) != checksums[relative_file_name_nocase]:
                            Logger.debug('check_mod_directories: File {} exists but its hash differs from expected.'.format(relative_file_name_nocase))
                            Logger.debug('check_mod_directories: Expected: {}, computed: {}'.format(checksums[relative_file_name_nocase].encode('hex'), sha1(full_file_path).encode('hex')))
                            return False

                        continue  # File present in the torrent, nothing to see here

                    if on_superfluous == 'remove':
                        Logger.debug('check_mod_directories: Removing file: {}'.format(full_file_path))
                        _safer_unlink(full_base_path, full_file_path)

                    elif on_superfluous == 'warn':
                        Logger.debug('check_mod_directories: Superfluous file: {}'.format(full_file_path))
                        return False

                    elif on_superfluous == 'ignore':
                        pass

                # Now check directories
                # Iterate over a copy because we'll be deleting items from the original
                for dir_name in dirnames[:]:
                    relative_dir_path = ccf(os.path.join(relative_path, dir_name))

                    if dir_name in WHITELIST_NAME:
                        dirnames.remove(dir_name)

                        with ignore_exceptions(KeyError):
                            dirs.remove(relative_dir_path)

                        continue

                    Logger.debug('check_mod_directories: Checking dir: {}'.format(relative_dir_path))
                    if relative_dir_path in dirs:
                        dirs.remove(relative_dir_path)
                        continue  # Directory present in the torrent, nothing to see here

                    full_directory_path = os.path.join(dirpath, dir_name)

                    if on_superfluous == 'remove':
                        Logger.debug('check_mod_directories: Removing directory: {}'.format(full_directory_path))
                        dirnames.remove(dir_name)

                        _safer_rmtree(full_base_path, full_directory_path)

                    elif on_superfluous == 'warn':
                        Logger.debug('check_mod_directories: Superfluous directory: {}'.format(full_directory_path))
                        return False

                    elif on_superfluous == 'ignore':
                        pass

        # Check for files missing on disk
        # file_paths contains all missing files OR files outside of any directory.
        # Such files will not exist with regular torrents but may happen if using
        # check_subdir != ''.
        # We just check if they exist. No deleting!
        for file_entry_nocase in file_paths:
            full_path = os.path.join(base_directory, file_entry_nocase)

            if not os.path.isfile(full_path):
                Logger.debug('check_mod_directories: File paths missing on disk, setting retval to False')
                Logger.debug('check_mod_directories: ' + full_path)
                success = False
                break

            if checksums and sha1(full_path) != checksums[file_entry_nocase]:
                Logger.debug('check_mod_directories: File {} exists but its hash differs from expected.'.format(file_entry_nocase))
                Logger.debug('check_mod_directories: Expected: {}, computed: {}'.format(checksums[file_entry_nocase].encode('hex'), sha1(full_path).encode('hex')))
                success = False
                break

        if dirs:
            Logger.debug('check_mod_directories: Dirs missing on disk, setting retval to False')
            Logger.debug('check_mod_directories: ' + ', '.join(dirs))
            success = False

    except OSError:
        success = False

    return success


def parse_files_list(files_list, checksums, only_subdir=''):
    """Computes the top directories, directories and the file paths contained in a torrent."""

    file_paths = set()
    dirs = set()
    top_dirs = set()

    # if only_subdir == 'foo/bar':
    #     'foo/bar/dir/file' => 'dir/file'
    if only_subdir != '':
        if not only_subdir.endswith(os.path.sep):
            only_subdir += os.path.sep

        subdir_len = len(only_subdir)

        # Shorten file names by removing the subdir from the begining
        files_list = [f[subdir_len:] for f in files_list if f.startswith(only_subdir)]
        if checksums:
            # Do the same for checksums keys. Keep hashes intact
            checksums = dict([(f[subdir_len:], hsh) for (f, hsh) in checksums.iteritems() if f.startswith(only_subdir)])

    for torrent_file in files_list:
        file_paths.add(torrent_file)
        dir_path = os.path.dirname(torrent_file)

        while dir_path:  # Go up the directory structure until the end
            if dir_path in dirs:  # If already processed for another file
                break

            dirs.add(dir_path)
            parent_dir = os.path.dirname(dir_path)
            if not parent_dir:
                top_dirs.add(dir_path)

            dir_path = parent_dir

    return top_dirs, dirs, file_paths, checksums


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
            file_stat = os.lstat(full_file_path)
        except OSError:
            Logger.error('check_files_mtime_correct: Could not perform stat on {}'.format(full_file_path))
            return False

        # Logger.debug('check_files_mtime_correct: {} {} {}'.format(file_path, file_stat.st_mtime, mtime))
        # Values for st_size and st_mtime based on libtorrent/src/storage.cpp: 135-190 // match_filesizes()
        if file_stat.st_size < size:  # Actually, not sure why < instead of != but kept this to be compatible with libtorrent
            Logger.debug('check_files_mtime_correct: Incorrect file size for {}'.format(full_file_path))
            return False

        # Allow for 1 sec discrepancy due to FAT32
        # Also allow files to be up to 5 minutes more recent than stated
        if int(file_stat.st_mtime) > mtime + 5 * 60 or int(file_stat.st_mtime) < mtime - 1:
            Logger.debug('check_files_mtime_correct: Incorrect modification time for {}'.format(full_file_path))
            return False

    return True


def is_ts3_plugin_installed(ts3_plugin_full_path):
    """Check if the given .ts3_plugin file is installed."""

    teamspeak_paths = teamspeak.get_plugins_locations()

    for teamspeak_path in teamspeak_paths:
        Logger.debug('is_ts3_plugin_installed: Checking if TS3 plugin is installed in {}'.format(teamspeak_path))
        checksums = teamspeak.compute_checksums_for_ts3_plugin(ts3_plugin_full_path)
        retval = check_mod_directories(checksums.keys(), base_directory=teamspeak_path,
                                       on_superfluous='ignore', checksums=checksums)

        if retval:
            Logger.info('is_ts3_plugin_installed: TS3 plugin found in {}'.format(teamspeak_path))
            return True

    Logger.info('is_ts3_plugin_installed: TS3 plugin not found in searched directories')
    return False


def are_ts_plugins_installed(mod_parent_location, file_paths):
    """Check if all ts3_plugin files contained inside the mod files are
    installed.
    """

    # teamspeak_path = teamspeak.get_install_location()

    for file_path in file_paths:
        if not file_path.endswith('.ts3_plugin'):
            continue

        file_location = os.path.join(mod_parent_location, file_path)
        retval = is_ts3_plugin_installed(file_location)

        if not retval:
            return retval

    return True


    # If the checked mod is not TFR, happily return rainbows and unicorns
#     if not mod_name.startswith("Task Force Arrowhead Radio"):
#         if mod_name != "@task_force_radio":
#             return True
#
#     teamspeak_plugins = os.path.join(teamspeak_path, 'plugins')
#     retval = check_mod_directories(file_paths, base_directory=teamspeak_plugins,
#                                    check_subdir='@task_force_radio\\TeamSpeak 3 Client\\plugins',
#                                    on_superfluous='ignore', checksums=checksums)
#
#     Logger.debug('are_ts_plugins_installed: Teamspeak plugins synchronized: {}'.format(retval))
#
#     return retval
