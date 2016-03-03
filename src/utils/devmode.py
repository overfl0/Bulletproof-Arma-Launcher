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

import json

from utils.paths import get_external_executable_path

DEVMODE_FILE_NAME = 'devmode.conf'

# class DevModeException(Exception):
#    pass


class DevMode(object):
    '''
    This is a simple class that loads a json file and allows access to its elements
    with a get_<element_name>() getter.
    If not found, the getter returns None or the <default> argument passed to the getter.

    Usage: devmode.get_something()           -> <something> or <None> if doesn't exist.
           devmode.get_sth_else(default=123) -> <sth_else> or <123> if doesn't exist.
    '''

    def __init__(self):
        try:
            devmode_file_path = get_external_executable_path(DEVMODE_FILE_NAME)
            with file(devmode_file_path, "rb") as f:
                s = f.read()
                self.devdata = json.loads(s)

        except ValueError:  # Bad JSON data
            raise
        #    raise DevModeException(ex)  # Note to self:
        # Do NOT throw exceptions like this! You'll lose stacktrace information!

        except Exception:
            self.devdata = {}

    def __getattribute__(self, name):
        if name.startswith("get_"):
            return lambda default = None: self.devdata.get(name[4:], default)

        return object.__getattribute__(self, name)

devmode = DevMode()
