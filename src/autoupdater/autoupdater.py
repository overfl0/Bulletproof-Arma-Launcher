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

# Allow relative imports when the script is run from the command line
if __name__ == "__main__":
    import os, sys
    file_directory = os.path.dirname(os.path.realpath(__file__))
    sys.path.append(os.path.abspath(os.path.join(file_directory, '..')))

"""
os.unlink on file which requires admin permissions:             WindowsError: [Error 5] Access is denied:
os.unlink on file which requires admin permissions and running: WindowsError: [Error 5] Access is denied:
os.unlink on file running:                                      WindowsError: [Error 32] The process cannot access the file because it is being used by another process:
file(a, "wb") on file running:                                  IOError: [Errno 13] Permission denied:

To know if we need UAC, check if the directory is writable
"""

import hashlib
import os
import shutil
import subprocess
import sys
import time

from kivy.logger import Logger

'''
try:
    WindowsError
except NameError:
    # We're on linux. Create a false exception that will never be raised so we can safely catch it and
    # handle the errors on Windows
    class WindowsError(Exception):
        pass
'''

def get_my_executable_name():
    return sys.argv[0]

def get_my_executable_pathname():
    return os.path.realpath(get_my_executable_name())

def call_file_arguments(filename):
    """Prepare arguments to call filename. Basically if it's a python script prepend 'python' to it."""
    if filename.endswith('.py'):
        return ['python', filename]

    return [filename]

def request_my_update(new_executable):
    """Update the executable being run with a new executable pointed by new_executable.
    The new_executable will be run with the path to this executable and a parameter indicating
    that an update has to take place."""
    my_executable_path = get_my_executable_pathname()

    args = call_file_arguments(new_executable)
    args.extend(['--', '-u', my_executable_path])

    Logger.info('Will call with args: ' + str(args))
    popen_object = subprocess.Popen(args)
    #Logger.info('Got: %s' % popen_object)
    # TODO: Error handling

def compare_if_same_files(other_executable):
    """This function checks if the running executable is the same as the one pointed by
    other_executable variable"""
    my_sha1 = None
    other_sha1 = None

    my_executable_path = get_my_executable_pathname()
    Logger.info("Comparing {} with {}...".format(my_executable_path, other_executable))

    try:
        with file(my_executable_path, "rb") as my_file:
            contents = my_file.read()
            my_sha1 = hashlib.sha1(contents).hexdigest()

        with file(other_executable, "rb") as other_file:
            contents = other_file.read()
            other_sha1 = hashlib.sha1(contents).hexdigest()

    except Exception as ex:
        print ex.message

    return my_sha1 == other_sha1

def try_perform_substitution(old_executable_name):
    my_executable_pathname = get_my_executable_pathname()
    Logger.info("me: " + my_executable_pathname)
    print "me: " + my_executable_pathname

    try:
        shutil.copy2(my_executable_pathname, old_executable_name)
        Logger.info("Copied!")
        return True

    except IOError as e:
        return False

def run_updated(old_executable_name):
    Logger.info('old: ' + old_executable_name)
    args = call_file_arguments(old_executable_name)

    popen_object = subprocess.Popen(args)

def perform_elevated_substitution():
    raise NotImplementedError()

if __name__ == '__main__':
    if parent:
        new_executable = os.path.join('new', 'autoupdtr.exe')
        update_me(new_executable)
        sys.exit(0)

    if child:
        #Logger.info('run')
        old_executable_name = sys.argv[1]
        perform_substitution(old_executable_name)
        run_updated(old_executable_name)
        sys.exit(0)

