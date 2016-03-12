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

import os
import psutil
import sys
import unicode_helpers


def program_running(executable):
    """Return if any process running on the system matches the given name."""

    executable_casefold = unicode_helpers.casefold(executable)

    for process in psutil.process_iter():
        try:
            name = unicode_helpers.fs_to_u(process.name())
            if unicode_helpers.casefold(name) == executable_casefold:
                return True

        except psutil.Error:
            continue

    return False


def file_running(path):
    """Return if any process running on the system matches the file path.
    This makes sure the process is running from the very same file instead of
    a file with merely the same name as the one requested.
    """

    real_path_casefold = unicode_helpers.casefold(os.path.realpath(path))

    for process in psutil.process_iter():
        try:
            exe_path = unicode_helpers.fs_to_u(process.exe())
            if unicode_helpers.casefold(os.path.realpath(exe_path)) == real_path_casefold:
                return True

        except psutil.Error:
            continue

    return False
