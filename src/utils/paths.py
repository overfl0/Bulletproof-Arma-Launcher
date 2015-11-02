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
import sys, os

def is_pyinstaller_bundle():
    """Is the program ran as a PyInstaller bundle? (as opposed to a simple python script)"""
    return getattr(sys, 'frozen', False)

def get_base_path(*relative):
    """Returns the path relative to the topmost directory in the program.
    Relative is optional. If relative is not passed, returns the path to the topmost directory in the program."""
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        launcher_py_path = os.path.dirname(os.path.realpath(sys.argv[0]))
        base_path = os.path.dirname(launcher_py_path)

    return os.path.join(base_path, *relative)


def get_source_path(*relative):
    """Returns the path relative to the source directory of the program.
    Relative is optional. If relative is not passed, Returns the path to the source directory of the program."""
    if is_pyinstaller_bundle():
        return get_base_path(*relative)
    else:
        return get_base_path('src', *relative)


def get_resources_path(*relative):
    """Returns the path relative to the resources directory of the program.
    Relative is optional. If relative is not passed, Returns the path to the resources directory of the program."""
    if is_pyinstaller_bundle():
        return get_base_path(*relative)
    else:
        return get_base_path('resources', *relative)


def is_dir_writable(path):
    """Checks if the directory passed as the argument is writable.
    Actually, the only portable and correct way to do this is to create a
    temporary file inside the directory and check if that succeeds."""

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

    except:  # If anything bad happens, stay on the safe side
        return False

    return True

def mkdir_p(path):
    """Create all directories described by path if they don't exist"""
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise
