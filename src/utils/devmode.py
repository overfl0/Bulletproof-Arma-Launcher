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

class DevModeException(Exception):
    pass

class DevMode(object):
    '''
    This is a simple class that loads a json file and allows access to its elements
    with a get_<element_name>() getter.
    If not found, the getter returns None.
    '''

    def __init__(self):
        try:
            devmode_file_path = get_external_executable_path(DEVMODE_FILE_NAME)
            with file(devmode_file_path, "rb") as f:
                s = f.read()
                self.devdata = json.loads(s)

        except ValueError as ex:  # Bad JSON data
            raise DevModeException(ex)

        except:
            self.devdata = {}

    def __getattribute__(self, name):
        if name.startswith("get_"):
            return lambda: object.__getattribute__(self, 'devdata').get(name[4:])

        return object.__getattribute__(self, name)

devmode = DevMode()
