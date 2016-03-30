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
import stat

from kivy.logger import Logger
from third_party.arma import Arma
from utils import unicode_helpers
from utils.context import ignore_exceptions
from utils.hashes import sha1
from utils.metadatafile import MetadataFile
from third_party import teamspeak


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


def filter_out_whitelisted(elements, whitelist):
    for whitelist_element in whitelist:
        file_match = os.path.sep + whitelist_element
        dir_match = os.path.sep + whitelist_element + os.path.sep
        elements = set(itertools.ifilterfalse(lambda x: x.endswith(file_match) or dir_match in x, elements))

    return elements


def check_mod_directories(files_list, base_directory, check_subdir='', on_superfluous='warn', checksums=None):
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
    This function will skip files or directories that match the 'whitelist' variable.

    If the dictionary checksums is not None, the files' checksums will be checked.

    Returns if the directory has been cleaned sucessfully or if all files present
    are supposed to be there. Do not ignore this value!
    If unsuccessful at removing files, the mod should NOT be considered ready to play."""

    if on_superfluous not in ('warn', 'remove', 'ignore'):
        raise Exception('Unknown action: {}'.format(on_superfluous))

    # Whitelist our and PWS metadata files
    whitelist = (MetadataFile.file_name, 'tfr.ts3_plugin', '.synqinfo', '.sync')

    top_dirs, dirs, file_paths, checksums = parse_files_list(files_list, checksums, check_subdir)

    # Remove whitelisted items from the lists
    dirs = filter_out_whitelisted(dirs, whitelist)
    file_paths = filter_out_whitelisted(file_paths, whitelist)

    base_directory = os.path.realpath(base_directory)
    Logger.debug('Verifying base_directory: {}'.format(base_directory))
    success = True

    try:
        for directory in top_dirs:
            with ignore_exceptions(KeyError):
                dirs.remove(directory)

            if directory in whitelist:
                continue

            full_base_path = os.path.join(base_directory, directory)
            _unlink_safety_assert(base_directory, full_base_path, action='enter')
            for (dirpath, dirnames, filenames) in os.walk(full_base_path, topdown=True, onerror=_raiser, followlinks=False):
                relative_path = os.path.relpath(dirpath, base_directory)
                Logger.debug('In directory: {}'.format(relative_path))

                # First check files in this directory
                for file_name in filenames:
                    relative_file_name = os.path.join(relative_path, file_name)

                    if file_name in whitelist:
                        Logger.debug('File {} in whitelist, skipping...'.format(file_name))

                        with ignore_exceptions(KeyError):
                            file_paths.remove(relative_file_name)
                        continue

                    full_file_path = os.path.join(dirpath, file_name)

                    Logger.debug('Checking file: {}'.format(relative_file_name))
                    if relative_file_name in file_paths:
                        file_paths.remove(relative_file_name)
                        Logger.debug('{} present in torrent metadata'.format(relative_file_name))

                        if checksums and sha1(full_file_path) != checksums[relative_file_name]:
                            Logger.debug('File {} exists but its hash differs from expected.'.format(relative_file_name))
                            Logger.debug('Expected: {}, computed: {}'.format(checksums[relative_file_name].encode('hex'), sha1(full_file_path).encode('hex')))
                            return False

                        continue  # File present in the torrent, nothing to see here

                    if on_superfluous == 'remove':
                        Logger.debug('Removing file: {}'.format(full_file_path))
                        _safer_unlink(full_base_path, full_file_path)

                    elif on_superfluous == 'warn':
                        Logger.debug('Superfluous file: {}'.format(full_file_path))
                        return False

                    elif on_superfluous == 'ignore':
                        pass

                # Now check directories
                # Iterate over a copy because we'll be deleting items from the original
                for dir_name in dirnames[:]:
                    relative_dir_path = os.path.join(relative_path, dir_name)

                    if dir_name in whitelist:
                        dirnames.remove(dir_name)

                        with ignore_exceptions(KeyError):
                            dirs.remove(relative_dir_path)

                        continue

                    Logger.debug('Checking dir: {}'.format(relative_dir_path))
                    if relative_dir_path in dirs:
                        dirs.remove(relative_dir_path)
                        continue  # Directory present in the torrent, nothing to see here

                    full_directory_path = os.path.join(dirpath, dir_name)

                    if on_superfluous == 'remove':
                        Logger.debug('Removing directory: {}'.format(full_directory_path))
                        dirnames.remove(dir_name)

                        _safer_rmtree(full_base_path, full_directory_path)

                    elif on_superfluous == 'warn':
                        Logger.debug('Superfluous directory: {}'.format(full_directory_path))
                        return False

                    elif on_superfluous == 'ignore':
                        pass

        # Check for files missing on disk
        # file_paths contains all missing files OR files outside of any directory.
        # Such files will not exist with regular torrents but may happen if using
        # check_subdir != ''.
        # We just check if they exist. No deleting!
        for file_entry in file_paths:
            full_path = os.path.join(base_directory, file_entry)

            if not os.path.isfile(full_path):
                Logger.debug('File paths missing on disk, setting retval to False')
                Logger.debug(full_path)
                success = False
                break

            if checksums and sha1(full_path) != checksums[file_entry]:
                Logger.debug('File {} exists but its hash differs from expected.'.format(file_entry))
                Logger.debug('Expected: {}, computed: {}'.format(checksums[file_entry].encode('hex'), sha1(full_path).encode('hex')))
                success = False
                break

        if dirs:
            Logger.debug('Dirs missing on disk, setting retval to False')
            Logger.debug(', '.join(dirs))
            success = False

    except OSError:
        success = False

    return success


def set_files_to_read_write(base_directory, files_list):
    """Ensures all the files have the write bit set. Useful if some external
    has set them to read-only.
    """

    Logger.info('Integrity: Checking read-write file access in directory: {}.'.format(base_directory))
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
                if ex.errno == errno.EPERM:  # 13
                    raise('TODO: Permission denied - admin required')
                else:
                    raise


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
            file_stat = os.stat(full_file_path)
        except OSError:
            Logger.error('Could not perform stat on {}'.format(full_file_path))
            return False

        # Logger.debug('{} {} {}'.format(file_path, file_stat.st_mtime, mtime))
        # Values for st_size and st_mtime based on libtorrent/src/storage.cpp: 135-190 // match_filesizes()
        if file_stat.st_size < size:  # Actually, not sure why < instead of != but kept this to be compatible with libtorrent
            Logger.debug('Incorrect file size for {}'.format(full_file_path))
            return False

        # Allow for 1 sec discrepancy due to FAT32
        # Also allow files to be up to 5 minutes more recent than stated
        if int(file_stat.st_mtime) > mtime + 5 * 60 or int(file_stat.st_mtime) < mtime - 1:
            Logger.debug('Incorrect modification time for {}'.format(full_file_path))
            return False

    return True


def is_complete_tfr_hack(mod_name, file_paths, checksums):
    """This is a hackish check if Task Force Arrowhead Radio mod has been
    correctly installed.
    To be fully installed, files contained in the userconfig subdirectory
    must be present in in Arma 3/userconfig directory. Additionally, a check
    if plugins have been copied to Teamspeak directory is made.
    """

    # If the checked mod is not TFR, happily return rainbows and unicorns
    if not mod_name.startswith("Task Force Arrowhead Radio"):
        return True

    arma_path = Arma.get_installation_path()
    userconfig = os.path.join(arma_path, 'userconfig')

    retval = check_mod_directories(file_paths, base_directory=userconfig,
                                   check_subdir='@task_force_radio\\userconfig',
                                   on_superfluous='ignore')

    if not retval:
        Logger.debug('TFR userconfig not populated. Marking as not fully installed')
        return retval
    else:
        Logger.debug('TFR userconfig files OK.')

    teamspeak_path = teamspeak.get_install_location()
    teamspeak_plugins = os.path.join(teamspeak_path, 'plugins')
    retval = check_mod_directories(file_paths, base_directory=teamspeak_plugins,
                                   check_subdir='@task_force_radio\\TeamSpeak 3 Client\\plugins',
                                   on_superfluous='ignore', checksums=checksums)

    Logger.debug('Teamspeak plugins synchronized: {}'.format(retval))

    return retval
