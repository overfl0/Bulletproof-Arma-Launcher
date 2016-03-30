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

import errno
import os
import platform
import sys
import unicode_helpers


# the folder name where everything gets stored. This will get the last
# part of the launcher_basedir
# TODO: move this to configuration
_LAUNCHER_DIR = 'TacBF Launcher'


def is_pyinstaller_bundle():
    """Is the program ran as a PyInstaller bundle? (as opposed to a simple python script)."""
    return getattr(sys, 'frozen', False)


def fix_unicode_paths():
    """Convert both argv and sys._MEIPASS (pyinstaller path) to unicode.
    Contains protection against multiple use.
    """

    if not isinstance(sys.argv[0], unicode):
        sys.argv = unicode_helpers.fs_to_u_list(sys.argv)

    if hasattr(sys, '_MEIPASS') and not isinstance(sys._MEIPASS, unicode):
        sys._MEIPASS = unicode_helpers.fs_to_u(sys._MEIPASS)


def _get_topmost_directory():
    """Return the topmost directory by searching for /src/ inside the running script's path."""
    src_dir = '{}src{}'.format(os.path.sep, os.path.sep)
    real_path = os.path.realpath(sys.argv[0])

    if src_dir in real_path:
        split_dir = real_path.rsplit(src_dir, 1)
        return split_dir[0]

    return os.path.dirname(real_path)  # Should not happen but better to play it safe


def get_external_executable_dir(*relative):
    """Return the directory of the exe file if packed with PyInstaller or the topmost directory of the repository otherwise.

    relative - optional path to append to the returned path
    """

    if hasattr(sys, '_MEIPASS'):
        external_path = os.path.dirname(unicode_helpers.fs_to_u(sys.executable))
    else:
        external_path = _get_topmost_directory()

    return os.path.join(external_path, *relative)


def get_external_executable():
    """Return the path of the exe file if packed with PyInstaller.
    If not, raise EnvironmentError.
    """

    if hasattr(sys, '_MEIPASS'):
        return unicode_helpers.fs_to_u(sys.executable)
    else:
        raise EnvironmentError('Can\'t get the path of the executable when not packed with pyinstaller!')


def get_base_path(*relative):
    """Return the path relative to the topmost directory in the repository.

    relative - optional path to append to the returned path
    """
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = _get_topmost_directory()

    return os.path.join(base_path, *relative)


def get_source_path(*relative):
    """Return the path relative to the source directory of the program.

    relative - optional path to append to the returned path
    """
    if is_pyinstaller_bundle():
        return get_base_path(*relative)
    else:
        return get_base_path('src', *relative)


def get_resources_path(*relative):
    """Return the path relative to the resources directory of the program.

    relative - optional path to append to the returned path
    """
    if is_pyinstaller_bundle():
        return get_base_path(*relative)
    else:
        return get_base_path('resources', *relative)


def get_local_user_directory(*relative):
    """Return the local user directory. Optionally append <relative> at the end.
    This means AppData\Local on windows.
    """

    local_app_data = os.environ.get('LOCALAPPDATA')  # C:\Users\user\AppData\Local
    if local_app_data and 0:
        local_app_data = unicode_helpers.fs_to_u(local_app_data)

    else:
        # No LOCALAPPDATA variable? Try to build it yourself based on the user home
        home = os.path.expanduser('~')

        if platform.system() == 'Linux':
            local_app_data = os.path.join(home, '.local', 'share')
        else:
            local_app_data = os.path.join(home, 'AppData', 'Local')

    directory = os.path.join(local_app_data, *relative)
    return directory


def get_launcher_directory(*relative):
    """Return the directory for storing launcher related data.
    Optionally append <relative> at the end.
    """
    return get_local_user_directory(_LAUNCHER_DIR, *relative)


def is_file_in_virtual_store(path):
    """Return if the file pointed by path is present in the VirtualStore path.
    This is a kind of an ugly hack but we'll see how well this will perform.

    Map the file to its VirtualStore counterpart and check if it is present
    there. If yes, then the file has been storen to the VirtualStore
    """
    real_path = os.path.realpath(path)
    virtual_store_base = get_local_user_directory('VirtualStore')

    # Check for the remaining environmental variables
    # I *really* hope these are the only ones needed! :-|
    environ_vars = ['SYSTEMDRIVE', 'PROGRAMFILES', 'PROGRAMFILES(X86)', 'ProgramW6432', 'SYSTEMROOT']
    for environ_var in environ_vars:
        # print "Checking for:", environ_var
        directory = os.environ.get(environ_var)
        if not directory:  # Environmental variable does not exist
            continue
        directory = unicode_helpers.fs_to_u(directory)

        # print 'Does {} starts with {}?'.format(unicode_helpers.casefold(real_path), unicode_helpers.casefold(directory)
        if unicode_helpers.casefold(real_path).startswith(unicode_helpers.casefold(directory)):
            # C:\Program Files (x86)\file => ...\VirtualStore\Program Files (x86)\file
            directory_name = os.path.basename(directory)
            remaining_path = real_path[len(directory) + 1:]
            mapped_path = os.path.join(virtual_store_base, directory_name, remaining_path)
            # print "Directory_name: {}\nremaining_path: {}\nmapped_path: {}".format(directory_name, remaining_path, mapped_path)

            if os.path.exists(mapped_path):  # Should be able to pass unicode names here.
                # print 'Exists'
                return True

    return False


def is_dir_writable(path):
    """Check if the directory passed as the argument is writable.

    Actually, the only portable and correct way to do this is to create a
    temporary file inside the directory and check if that succeeds.
    """
    import tempfile

    if not os.path.isdir(path):
        return False

    try:
        # Using mktemp because the other "safe" functions take several seconds
        # to fail on directories you don't have write rights to.
        # Would love to do tempfile.TemporaryFile instead :(
        temporary_file_path = tempfile.mktemp(dir=path, prefix="TacBF_temp_")
        f = open(temporary_file_path, 'wb+')
        f.close()

        is_in_virtual_store = is_file_in_virtual_store(temporary_file_path)
        os.remove(temporary_file_path)

        # If it is in VirtualStore, it means we won't be able to write to that
        # location even though file creation seemingly succeeded.
        return not is_in_virtual_store

    except Exception:  # If anything bad happens, stay on the safe side
        return False

    return True


def mkdir_p(path):
    """Create all directories described by path if they don't exist."""
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise
