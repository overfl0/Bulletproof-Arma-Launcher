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

# import Windows registry package while ensuring cygwin compatibility
try:
    import cygwinreg as _winreg
    KEY_WOW64_32KEY = 0x200  # Cygwin, you sucker!

except ImportError:
    import _winreg
    KEY_WOW64_32KEY = _winreg.KEY_WOW64_32KEY


class Registry(object):
    Error = OSError

    @staticmethod
    def ReadValue(super_key_handle, key_path, value_name, force_32bit=True):
        """Read the value value_name from the key key_path from Local Machine in the Registry.

        super_key_handle is an already open registry key or a predefined one (like HKEY_LOCAL_MACHINE).
        If force_32bit is set, it will force 32bit view of the registry."""

        flags = _winreg.KEY_READ
        if force_32bit:
            flags = flags | KEY_WOW64_32KEY

        key = _winreg.OpenKey(super_key_handle, key_path, 0, flags)
        (value, valuetype) = _winreg.QueryValueEx(key, value_name)
        key.Close()

        return value

    @staticmethod
    def ReadValueMachine(key_path, value_name, force_32bit=True):
        """Read the value value_name from the key key_path from Local Machine in the Registry.

        If force_32bit is set, it will force 32bit view of the registry."""

        return Registry.ReadValue(_winreg.HKEY_LOCAL_MACHINE, key_path, value_name, force_32bit)

    @staticmethod
    def ReadValueCurrentUser(key_path, value_name, force_32bit=True):
        """Read the value value_name from the key key_path from Local Machine in the Registry.

        If force_32bit is set, it will force 32bit view of the registry."""

        return Registry.ReadValue(_winreg.HKEY_CURRENT_USER, key_path, value_name, force_32bit)
