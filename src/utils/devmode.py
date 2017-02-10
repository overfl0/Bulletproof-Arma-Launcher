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

import json
import sys

from utils.paths import get_external_executable_dir
from utils.critical_messagebox import MessageBox

DEVMODE_FILE_NAME = 'devmode.conf'


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
            devmode_file_path = get_external_executable_dir(DEVMODE_FILE_NAME)
            with file(devmode_file_path, "rb") as f:
                s = f.read()
                self.devdata = json.loads(s)

        except ValueError as ex:  # Bad JSON data
            try:
                message = unicode(ex)
            except:
                message = unicode(repr(str(ex)))

            MessageBox('devmode.conf:\n' + message, 'devmode.conf contains an error!')
            sys.exit(1)

        except Exception:
            self.devdata = {}

    def __getattribute__(self, name):
        if name.startswith("get_"):
            return lambda default = None, mandatory = False: self.devdata[name[4:]] if mandatory else self.devdata.get(name[4:], default)

        return object.__getattribute__(self, name)

devmode = DevMode()
