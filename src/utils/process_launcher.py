# Bulletproof Arma Launcher
# Copyright (C) 2017 Lukasz Taczuk
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

import subprocess
import textwrap
import unicode_helpers

from utils.critical_messagebox import MessageBox
from utils import admin

ADMIN_REQUIRED_MESSAGE = textwrap.dedent('''
    A program that requires administrator rights could not be run:

    {}

    THE LAUNCHER MAY WORK INCORRECTLY FROM THIS POINT ON!

    To fix this, either run the launcher as an administrator
    (not recommended) or reconfigure the program:

    -Right-click on the program
    -Select "Properties"
    -Open the "Compatibility" tab
    -Uncheck "Run this program as an Administrator
''')

def run(program_args, shell=False):
    """Run the given program with the given parameters.
    In case the program requires elevation, run an UAC prompt if on Windows.
    Returns a Popen or Popen compatible object.
    """

    fs_program_args = unicode_helpers.u_to_fs_list(program_args)

    try:
        return subprocess.Popen(fs_program_args, shell=shell)

    except WindowsError as ex:
        if ex.winerror != 740:  # The requested operation requires elevation
            raise

        # Try running as admin
        handle = admin.run_admin(program_args[0], program_args[1:])

        if not handle:
            MessageBox(ADMIN_REQUIRED_MESSAGE.format(program_args[0]), 'Error!')

        return handle
