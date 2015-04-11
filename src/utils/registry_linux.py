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

# Linux dummy implementation.

# Don't allow the use of this module on linux outside of unit tests
# import sys
# if "unittest" not in sys.modules.keys():
#     raise Exception("Registry not implemented on Linux. Dummy class for unit tests only!")

# Dummy class with fake methods
class Registry(object):
    Error = Exception

    @staticmethod
    def ReadValue(super_key_handle, key_path, value_name, force_32bit=True):
        return '/tmp'

    @staticmethod
    def ReadValueMachine(key_path, value_name, force_32bit=True):
        return '/tmp'

    @staticmethod
    def ReadValueCurrentUser(key_path, value_name, force_32bit=True):
        return '/tmp'
