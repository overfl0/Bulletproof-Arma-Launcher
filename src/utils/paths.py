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
import sys


def is_pyinstaller_bundle():
    """Is the program ran as a PyInstaller bundle? (as opposed to a simple python script)."""
    return getattr(sys, 'frozen', False)


def u_to_fs(args):
    """Convert a list of arguments from unicode to the file system encoding"""
    return [arg.encode(sys.getfilesystemencoding()) for arg in args]


def fs_to_u(args):
    """Convert a list of arguments from the file system encoding to unicode"""
    return [arg.decode(sys.getfilesystemencoding()) for arg in args]


def fix_unicode_paths():
    """Convert both argv and sys._MEIPASS (pyinstaller path) to unicode.
    Contains protection against multiple use.
    """

    if not isinstance(sys.argv[0], unicode):
        sys.argv = fs_to_u(sys.argv)

    if hasattr(sys, '_MEIPASS') and not isinstance(sys._MEIPASS, unicode):
        sys._MEIPASS = sys._MEIPASS.decode(sys.getfilesystemencoding())


def _get_topmost_directory():
    """Return the topmost directory by searching for /src/ inside the running script's path."""
    src_dir = '{}src{}'.format(os.path.sep, os.path.sep)
    real_path = os.path.realpath(sys.argv[0])

    if src_dir in real_path:
        split_dir = real_path.rsplit(src_dir, 1)
        return split_dir[0]

    return os.path.dirname(real_path)  # Should not happen but better to play it safe


def get_external_executable_path(*relative):
    """Return the path of the exe file if packed with PyInstaller or the topmost directory of the repository otherwise.

    relative - optional path to append to the returned path
    """

    if hasattr(sys, '_MEIPASS'):
        external_path = os.path.dirname(sys.executable.decode(sys.getfilesystemencoding()))
    else:
        external_path = _get_topmost_directory()

    return os.path.join(external_path, *relative)


def get_external_executable():
    """Return the path of the exe file if packed with PyInstaller.
    If not, raise EnvironmentError.
    """

    if hasattr(sys, '_MEIPASS'):
        return sys.executable.decode(sys.getfilesystemencoding())
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
        os.remove(temporary_file_path)

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
