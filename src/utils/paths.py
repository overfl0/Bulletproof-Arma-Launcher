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
