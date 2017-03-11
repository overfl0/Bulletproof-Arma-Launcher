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
    import os
    import sys
    file_directory = os.path.dirname(os.path.realpath(__file__))
    sys.path.append(os.path.abspath(os.path.join(file_directory, '..')))

"""
os.unlink on file which requires admin permissions:             WindowsError: [Error 5] Access is denied:
os.unlink on file which requires admin permissions and running: WindowsError: [Error 5] Access is denied:
os.unlink on file running:                                      WindowsError: [Error 32] The process cannot access the file because it is being used by another process:
file(a, "wb") on file running:                                  IOError: [Errno 13] Permission denied:
file(a, "wb") on file which requires admin NOT running:         IOError: [Errno 13] Permission denied:

To know if we need UAC, check if the directory is writable
"""

import hashlib
import os
import shutil
import sys

from distutils.version import LooseVersion
from kivy.logger import Logger
from utils.devmode import devmode
from utils import paths
from utils import process_launcher
from utils import unicode_helpers

'''
try:
    WindowsError
except NameError:
    # We're on linux. Create a false exception that will never be raised so we can safely catch it and
    # handle the errors on Windows
    class WindowsError(Exception):
        pass
'''


class UpdateException(Exception):
    pass


def get_external_executable():
    executable = devmode.get_application_executable()
    if executable:
        return executable

    else:
        return paths.get_external_executable()


def call_file_arguments(filename):
    """Prepare arguments to call filename. Basically if it's a python script prepend 'python' to it."""
    if filename.endswith('.py'):
        return ['python', filename]

    return [filename]


def require_admin_privileges():
    """Check if the process can overwrite the executable being run or if it needs extra priviledges.
    For now, this will just get the directory of the executable and try to
    create a dummy file in there. We assume the executable will have the same
    permissions as every file in the same directory.
    If a dummy file cannot be created, it means we probably need administrator
    provileges to perform the substitution.
    """

    my_executable_dir = os.path.dirname(get_external_executable())
    Logger.info('Autoupdater: executable dir: {}'.format(my_executable_dir))
    dir_is_writable = paths.is_dir_writable(my_executable_dir)
    Logger.info('Autoupdater: dir_is_writable: {}'.format(dir_is_writable))
    return not dir_is_writable


def request_my_update(new_executable):
    """Update the executable being run with a new executable pointed by new_executable.
    The new_executable will be run with the path to this executable and a parameter indicating
    that an update has to take place."""
    my_executable_path = get_external_executable()

    args = call_file_arguments(new_executable)
    args.extend(['--', '-u', my_executable_path])

    Logger.info('Autoupdater: Will call with args: [{}]'.format(', '.join(args)))
    process_launcher.run(args)


def compare_if_same_files(other_executable):
    """This function checks if the running executable is the same as the one pointed by
    other_executable variable"""
    my_sha1 = None
    other_sha1 = None

    my_executable_path = get_external_executable()
    Logger.info('Autoupdater: Comparing {} with {}...'.format(my_executable_path, other_executable))

    with file(my_executable_path, 'rb') as my_file:
        contents = my_file.read()
        my_sha1 = hashlib.sha1(contents).hexdigest()

    try:
        with file(other_executable, 'rb') as other_file:
            contents = other_file.read()
            other_sha1 = hashlib.sha1(contents).hexdigest()

    except IOError as ex:
        if ex.errno == 2:
            Logger.info('Autoupdater: Up to date file missing.')
            return False

    same_files = my_sha1 == other_sha1
    Logger.info('Autoupdater: Same files: {}'.format(same_files))
    return same_files


def perform_substitution(old_executable_name):
    my_executable_pathname = get_external_executable()
    Logger.info('Autoupdater: Trying to copy {} over {}'.format(my_executable_pathname, old_executable_name))

    try:
        shutil.copy2(my_executable_pathname, old_executable_name)
        Logger.info('Autoupdater: Success! File copied.')

    except IOError as ex:
        if ex.errno == 13:  # Permission denied
            raise UpdateException('Copying failed. Maybe you need Administrator rights?')

        raise


def run_updated(old_executable_name):
    Logger.info('Autoupdater: Running the updated file: {}'.format(old_executable_name))
    args = call_file_arguments(old_executable_name)

    process_launcher.run(args)


def should_update(u_from, u_to):
    """Compare the versions and tell if u_to is newer than u_from."""
    my_version = LooseVersion(u_from)
    proposed_version = LooseVersion(u_to)

    return proposed_version > my_version


if __name__ == '__main__':
    '''
    if parent:
        new_executable = os.path.join('new', 'autoupdtr.exe')
        update_me(new_executable)
        sys.exit(0)

    if child:
        #Logger.info('Autoupdater: run')
        old_executable_name = sys.argv[1]
        perform_substitution(old_executable_name)
        run_updated(old_executable_name)
        sys.exit(0)

    '''
