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

import errno
import os
import stat
import subprocess
import sys
import textwrap

import libtorrent
from kivy.logger import Logger

from sync.integrity import check_mod_directories, check_files_mtime_correct, are_ts_plugins_installed, is_whitelisted
from utils import paths
from utils import unicode_helpers
from utils import walker
from utils.metadatafile import MetadataFile


class AdminRequiredError(Exception):
    pass


def set_torrent_complete(mod):
    metadata_file = MetadataFile(mod.foldername)
    metadata_file.read_data(ignore_open_errors=True)
    metadata_file.set_dirty(False)
    metadata_file.set_torrent_url(mod.torrent_url)
    metadata_file.set_torrent_content(mod.torrent_content)
    metadata_file.set_torrent_resume_data('')

    metadata_file.set_force_creator_complete(True)
    metadata_file.write_data()


def is_complete_quick(mod):
    """Performs a quick check to see if the mod *seems* to be correctly installed.
    This check assumes no external changes have been made to the mods.

    1. Check if metadata file exists and can be opened (instant)
    1a. WORKAROUND: Check if the file has just been created so it must be complete
    2. Check if torrent is not dirty [download completed successfully] (instant)
    3. Check if torrent url matches (instant)
    4. Check if files have the right size and modification time (very quick)
    5. Check if there are no superfluous files in the directory (very quick)"""

    Logger.info('Is_complete: Checking mod {} for completeness...'.format(mod.foldername))

    metadata_file = MetadataFile(mod.foldername)

    # (1) Check if metadata can be opened
    try:
        metadata_file.read_data(ignore_open_errors=False)
    except (IOError, ValueError):
        Logger.info('Is_complete: Metadata file could not be read successfully. Marking as not complete')
        return False

    # Workaround
    if metadata_file.get_force_creator_complete():
        Logger.info('Is_complete: Torrent marked as (forced) complete by the creator. Treating as complete')
        return True

    # (2)
    if metadata_file.get_dirty():
        Logger.info('Is_complete: Torrent marked as dirty (not completed successfully). Marking as not complete')
        return False

    # (3)
    if metadata_file.get_torrent_url() != mod.torrent_url:
        Logger.info('Is_complete: Torrent urls differ. Marking as not complete')
        return False

    # Get data required for (4) and (5)
    torrent_content = metadata_file.get_torrent_content()
    if not torrent_content:
        Logger.info('Is_complete: Could not get torrent file content. Marking as not complete')
        return False

    try:
        torrent_info = get_torrent_info_from_bytestring(torrent_content)
    except RuntimeError:
        Logger.info('Is_complete: Could not parse torrent file content. Marking as not complete')
        return False

    resume_data_bencoded = metadata_file.get_torrent_resume_data()
    if not resume_data_bencoded:
        Logger.info('Is_complete: Could not get resume data. Marking as not complete')
        return False
    resume_data = libtorrent.bdecode(resume_data_bencoded)

    # (4)
    file_sizes = resume_data['file sizes']
    files = torrent_info.files()
    # file_path, size, mtime
    files_data = map(lambda x, y: (y.path.decode('utf-8'), x[0], x[1]), file_sizes, files)

    if not check_files_mtime_correct(mod.parent_location, files_data):
        Logger.info('Is_complete: Some files seem to have been modified in the meantime. Marking as not complete')
        return False

    # (5) Check if there are no additional files in the directory
    # TODO: Check if these checksums are even needed now
    checksums = dict([(entry.path.decode('utf-8'), entry.filehash.to_bytes()) for entry in torrent_info.files()])
    files_list = checksums.keys()
    if not check_mod_directories(files_list, mod.parent_location, on_superfluous='warn'):
        Logger.info('Is_complete: Superfluous files in mod directory. Marking as not complete')
        return False

    if not are_ts_plugins_installed(mod.parent_location, files_list):
        Logger.info('Is_complete: TS plugin out of date or not installed.')
        return False

    return True


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


def get_admin_error(text, path):
    error_message = textwrap.dedent('''
        Error: {}:
        {}

        Please fix the file permissions before continuing.

        This may also happen if the file is open by another program.
        Make sure that Steam is NOT updating files right now. Otherwise, wait
        until Steam finishes updating files and retry.

        If not, running the launcher as Administrator may help (not recommended).

        If you reinstalled your system lately, [ref=http://superuser.com/a/846155][color=3572b0]you may need to fix files ownership.[/color][/ref]
        ''').format(text, path)

    return error_message


def path_already_used_for_mod(path, all_existing_mods):
    """Check if a given path is already used by a mod and return its name.
    Return None otherwise.
    """

    path = unicode_helpers.casefold(os.path.realpath(path))

    for mod in all_existing_mods:
        mod_full_path = unicode_helpers.casefold(mod.get_full_path())
        mod_real_full_path = unicode_helpers.casefold(mod.get_real_full_path())
        if path == mod_full_path or \
           path == mod_real_full_path or \
           path.startswith(mod_full_path + os.path.sep) or \
           path.startswith(mod_real_full_path + os.path.sep):
            return mod.foldername

    return None


def path_can_be_a_mod(path, mods_directory):
    """Check if a given path could be used by a mod.
    path - patch to be checked.
    mods_directory - the directory where mods are stored by the launcher.
    """

    launcher_moddir = os.path.realpath(mods_directory)
    launcher_moddir_casefold = unicode_helpers.casefold(launcher_moddir)
    path_casefold = unicode_helpers.casefold(os.path.realpath(path))

    # Loop to parent (infinite loop)
    if launcher_moddir_casefold == path_casefold or \
       launcher_moddir_casefold.startswith(path_casefold + os.path.sep):
        Logger.info("path_can_be_a_mod: Rejecting {}. Loop to parent.".format(path_casefold))
        return False

    directory_name = os.path.basename(path_casefold)
    if not directory_name:  # Path ends with a '\' or '/'
        directory_name = os.path.dirname(path_casefold)

    # All names must be changed to lowercase
    bad_directories = [
        'steam',
        'steamapps',
        'workshop',
        'content',
        '107410',
        'common',
        'arma 3',
        'desktop',
    ]
    if directory_name in bad_directories:
        Logger.info("path_can_be_a_mod: Rejecting {}. Blacklisted directory.".format(path_casefold))
        return False

    if len(path_casefold) == 3 and path_casefold.endswith(':\\'):
        Logger.info("path_can_be_a_mod: Rejecting {}. Root directory.".format(path_casefold))
        return False

    if path_casefold == unicode_helpers.casefold(paths.get_user_home_directory()):
        Logger.info("path_can_be_a_mod: Rejecting {}. Home directory.".format(path_casefold))
        return False

    return True


def set_node_read_write(node_path):
    """Set file or directory to read-write by removing the read-only bit."""

    fs_node_path = unicode_helpers.u_to_fs(node_path)

    try:
        stat_struct = os.lstat(fs_node_path)

    except OSError as e:
        Logger.error('Torrent_utils: exception')
        if e.errno == errno.ENOENT:  # 2 - File not found
            Logger.info('Torrent_utils: file not found')
            return
        raise

    # If the file is read-only to the owner, change it to read-write
    if not stat_struct.st_mode & stat.S_IWUSR:
        Logger.info('Integrity: Setting write bit to file: {}'.format(node_path))
        try:
            os.chmod(fs_node_path, stat_struct.st_mode | stat.S_IWUSR)

        except OSError as ex:
            if ex.errno == errno.EACCES:  # 13
                error_message = get_admin_error('file/directory is read-only and cannot be changed', node_path)
                Logger.error(error_message)
                raise AdminRequiredError(error_message)
            else:
                raise


def ensure_directory_exists(base_directory):
    """Ensure the directory passed as the argument exists.
    If the given directory is a broken Junction or Symlink, remove it.
    Then try creating the directory and if that fails, try to mitigate the problem
    by setting the parent directory to read-write and retrying the directory
    creation. If that fails, raise an AdminRequiredError.
    """

    try:
        if paths.is_broken_junction(base_directory):
            Logger.info('torrent_utils: Removing potentially broken Junction: {}'.format(base_directory))
            os.rmdir(base_directory)

        paths.mkdir_p(base_directory)

    except OSError:
        # Try fixing the situation by setting parent directory to read-write
        set_node_read_write(os.path.dirname(base_directory))

        try:
            # Try again
            if paths.is_broken_junction(base_directory):
                Logger.info('torrent_utils: Removing potentially broken Junction: {}'.format(base_directory))
                os.rmdir(base_directory)

            paths.mkdir_p(base_directory)

        except OSError:
            error_message = get_admin_error('directory cannot be created or is not valid', base_directory)
            Logger.error(error_message)
            raise AdminRequiredError(error_message)


def remove_broken_junction(path):
    try:
        if paths.is_broken_junction(path):
            os.rmdir(path)

    except OSError:
        error_message = get_admin_error('file/directory cannot be created or is not valid', path)
        Logger.error(error_message)
        raise AdminRequiredError(error_message)

def _replace_broken_junction_with_directory(path):
    """Perform a test whether the given path is a broken junction and fix it
    if it is.
    """

    if paths.is_broken_junction(path):
        ensure_directory_exists(path)
        set_node_read_write(path)


def ensure_directory_structure_is_correct(mod_directory):
    """Ensures all the files in the mod's directory have the write bit set and
    there are no broken Junctions nor Symlinks in the directory structure.
    Useful if some external tool has set them to read-only.
    """

    Logger.info('Torrent_utils: Checking read-write file access in directory: {}.'.format(mod_directory))

    set_node_read_write(mod_directory)
    _replace_broken_junction_with_directory(mod_directory)

    if not paths.is_dir_writable(mod_directory):
        error_message = get_admin_error('directory is not writable', mod_directory)
        raise AdminRequiredError(error_message)

    for (dirpath, dirnames, filenames) in walker.walk(mod_directory):
        # Needs to check the dirnames like this because if a child directory is
        # a broken junction, it's never going to be used as dirpath
        for node_name in dirnames:
            node_path = os.path.join(dirpath, node_name)
            Logger.info('Torrent_utils: Checking node: {}'.format(node_path))

            set_node_read_write(node_path)
            _replace_broken_junction_with_directory(node_path)

            if not paths.is_dir_writable(node_path):
                error_message = get_admin_error('directory is not writable', node_path)
                raise AdminRequiredError(error_message)

        for node_name in filenames:
            node_path = os.path.join(dirpath, node_name)
            Logger.info('Torrent_utils: Checking node: {}'.format(node_path))

            set_node_read_write(node_path)

            if not paths.is_file_writable(node_path):
                error_message = get_admin_error('file is not writable', node_path)
                raise AdminRequiredError(error_message)

def prepare_mod_directory(mod_full_path, check_writable=True):
    """Prepare the mod with the correct permissions, etc...
    This should make sure the parent directories are present, the mod directory
    is either not existing or it is present and has no broken symlinks.

    Right now, there is a lot of duplicate code in here, that will hopefully be
    refactored in the future, after the other features are implemented.
    """
    # TODO: Simplify all the calls and remove duplicate code
    parent_location = os.path.dirname(mod_full_path)

    # Ensure the base directory exists
    ensure_directory_exists(parent_location)
    set_node_read_write(parent_location)

    # If mod directory exists, check if it's valid
    if os.path.lexists(mod_full_path):
        if os.path.isdir(mod_full_path):
            remove_broken_junction(mod_full_path)
        else:
            # If it's not a directory, remove it because we need a dir here
            os.unlink(mod_full_path)

    if os.path.lexists(mod_full_path):
        if check_writable:
            # Read-write everything
            ensure_directory_structure_is_correct(mod_full_path)

    else:
        if not paths.is_dir_writable(parent_location):
            error_message = get_admin_error('directory is not writable', parent_location)
            raise AdminRequiredError(error_message)

def create_symlink(symlink_name, orig_path):
    """Create an NTFS Junction.
    For now, just use subprocess. Maybe switch to native libs later.
    """
    symlink_name_fs = unicode_helpers.u_to_fs(symlink_name)
    orig_path_fs = unicode_helpers.u_to_fs(orig_path)

    return subprocess.check_call([b'cmd', b'/c', b'mklink', b'/J', symlink_name_fs, orig_path_fs])

def symlink_mod(mod_full_path, real_location):
    """Set a new location for a mod.
    This includes making sure the mod is ready for being user afterwards.
    """

    if os.path.exists(mod_full_path):  # sometimes the junction may already exist
        try:
            os.rmdir(mod_full_path)

        except OSError as ex:
            if ex.errno != 41:  # TODO: Figure out which error this is
                raise

            # The directory is not empty

            # Really ugly workaround...
            import tkMessageBox
            import Tkinter

            root = Tkinter.Tk()
            root.withdraw()  # use to hide tkinter window

            message = textwrap.dedent('''\
            To perform this action, the following directory will first have to be completely deleted:
            {}

            Are you sure you want to continue?
            '''.format(mod_full_path))

            result = tkMessageBox.askquestion('Are you sure?', message, icon='warning', parent=root)
            if result == 'yes':
                import shutil
                try:
                    shutil.rmtree(mod_full_path)
                except:
                    message = textwrap.dedent('''
                    An error happened while deleting the directory:

                    {}

                    This may be because the laucnher does not have the permissions required.
                    You need to delete it manually to proceed.
                    ''').format(mod_full_path)

                    raise AdminRequiredError(message)
            else:
                return


    try:
        prepare_mod_directory(mod_full_path, check_writable=False)
        create_symlink(mod_full_path, real_location)
        prepare_mod_directory(mod_full_path)

    except:
        t, v, tb = sys.exc_info()

        try:
            os.rmdir(mod_full_path)
        except Exception as ex:
            Logger.error('symlink_mod: Error while deleting: {} {}'.format(mod_full_path, repr(ex)))

        raise t, v, tb

def create_add_torrent_flags(just_seed=False):
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
    if just_seed:
        flags |= f.flag_upload_mode
    # flags |= f.flag_share_mode
    flags |= f.flag_duplicate_is_error  # default?

    # no_recheck_incomplete_resume

    return flags


def create_torrent(directory, announces=None, output=None, comment=None, web_seeds=None):
    if not output:
        output = directory + ".torrent"

    # "If a piece size of 0 is specified, a piece_size will be calculated such that the torrent file is roughly 40 kB."
    piece_size_multiplier = 0
    piece_size = (16 * 1024) * piece_size_multiplier  # Must be multiple of 16KB

    # http://www.libtorrent.org/make_torrent.html#create-torrent
    flags = libtorrent.create_torrent_flags_t.calculate_file_hashes

    if not os.path.isdir(directory):
        raise Exception("The path {} is not a directory".format(directory))

    fs = libtorrent.file_storage()
    is_not_whitelisted = lambda node: not is_whitelisted(unicode_helpers.decode_utf8(node))
    libtorrent.add_files(fs, unicode_helpers.encode_utf8(directory), is_not_whitelisted, flags=flags)
    t = libtorrent.create_torrent(fs, piece_size=piece_size, flags=flags)

    for announce in announces:
        t.add_tracker(unicode_helpers.encode_utf8(announce))

    if comment:
        t.set_comment(unicode_helpers.encode_utf8(comment))

    for web_seed in web_seeds:
        t.add_url_seed(unicode_helpers.encode_utf8(web_seed))
    # t.add_http_seed("http://...")

    libtorrent.set_piece_hashes(t, unicode_helpers.encode_utf8(os.path.dirname(directory)))

    with open(output, "wb") as file_handle:
        file_handle.write(libtorrent.bencode(t.generate()))

    return output
