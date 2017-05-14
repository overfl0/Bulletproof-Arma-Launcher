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

import os
import psutil
import unicode_helpers

from kivy.logger import Logger


def program_running(*executable_names):
    """Return if any process running on the system matches the given names."""

    executables_casefold = [unicode_helpers.casefold(name) for name in executable_names]

    for process in psutil.process_iter():
        try:
            name = unicode_helpers.fs_to_u(process.name())
            if unicode_helpers.casefold(name) in executables_casefold:
                return True

        except psutil.Error:
            continue

    return False


def file_running(path):
    """Return if any process running on the system matches the file path.
    This makes sure the process is running from the very same file instead of
    a file with merely the same name as the one requested.

    ATTENTION: More often than not you will get a Permission Denied error which
    will prevent the code to retrieve the full path of the process!
    Thus the code will then think such a process is not running, which is false!

    Use program_running() unless you are 100% sure you will have access to the
    process you want to check.
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


def kill_program(executable_name):
    """Kill all the programs that match the given name."""

    executable_casefold = unicode_helpers.casefold(executable_name)
    Logger.info('Iterating processes in search for {}'.format(executable_name))

    for process in psutil.process_iter():
        try:
            name = unicode_helpers.fs_to_u(process.name())
            if unicode_helpers.casefold(name) == executable_casefold:
                Logger.info('Killing {}!'.format(name))
                process.kill()

        except psutil.Error:
            continue


def is_parent_running(retval_on_error=True):
    """Check if parent process is up and running"""

    try:
        return psutil.Process().parent() is not None

    except Exception as ex:
        Logger.error('is_parent_running: Got an exception while checking for the parent: {}. Returning: {}'.format(
            ex, retval_on_error))
        return retval_on_error
