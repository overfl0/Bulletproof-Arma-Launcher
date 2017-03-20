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

# import Windows registry package while ensuring cygwin compatibility
try:
    import cygwinreg as _winreg
    KEY_WOW64_64KEY = 0x100
    KEY_WOW64_32KEY = 0x200

except ImportError:
    import _winreg
    KEY_WOW64_64KEY = _winreg.KEY_WOW64_64KEY
    KEY_WOW64_32KEY = _winreg.KEY_WOW64_32KEY


class Registry(object):
    Error = OSError

    @staticmethod
    def _ReadValue(super_key_handle, key_path, value_name, force_32bit=False, force_64bit=False):
        """Read the value value_name from the key key_path from Local Machine in the Registry.

        super_key_handle is an already open registry key or a predefined one (like HKEY_LOCAL_MACHINE).
        If force_32bit is True, it will force 32bit view of the registry.
        If force_64bit is True, it will force 64bit view of the registry.
        """

        flags = _winreg.KEY_READ
        if force_32bit:
            flags = flags | KEY_WOW64_32KEY
        if force_64bit:
            flags = flags | KEY_WOW64_64KEY

        key = _winreg.OpenKey(super_key_handle, key_path, 0, flags)
        (value, valuetype) = _winreg.QueryValueEx(key, value_name)
        key.Close()

        return value

    @staticmethod
    def ReadValue(super_key_handle, key_path, value_name, check_both_architectures=False):
        """Read the value value_name from the key key_path from Local Machine in the Registry.

        super_key_handle is an already open registry key or a predefined one (like HKEY_LOCAL_MACHINE).
        If check_both_architectures is True, it will first check for a 64bit key
        and then for a 32bit key if no 64bit key is present.
        """

        if not check_both_architectures:
            return Registry._ReadValue(super_key_handle, key_path, value_name, force_32bit=False, force_64bit=False)

        try:
            return Registry._ReadValue(super_key_handle, key_path, value_name, force_64bit=True, force_32bit=False)
        except Registry.Error as ex:
            if ex.errno == 2:  # Key/file not found
                return Registry._ReadValue(super_key_handle, key_path, value_name, force_64bit=False, force_32bit=True)

            raise

    @staticmethod
    def ReadValueMachine(key_path, value_name, check_both_architectures=False):
        """Read the value value_name from the key key_path from Local Machine in the Registry.

        If check_both_architectures is True, it will first check for a 64bit key
        and then for a 32bit key if no 64bit key is present.
        """

        return Registry.ReadValue(_winreg.HKEY_LOCAL_MACHINE, key_path, value_name, check_both_architectures)

    @staticmethod
    def ReadValueCurrentUser(key_path, value_name, check_both_architectures=False):
        """Read the value value_name from the key key_path from Current User in the Registry.

        If check_both_architectures is True, it will first check for a 64bit key
        and then for a 32bit key if no 64bit key is present.
        """

        return Registry.ReadValue(_winreg.HKEY_CURRENT_USER, key_path, value_name, check_both_architectures)

    @staticmethod
    def ReadValueUserAndMachine(key_path, value_name, check_both_architectures=False):
        """Read the value value_name from the key key_path from Current User and
        then Local Machine if reading from current user failed.

        If check_both_architectures is True, it will first check for a 64bit key
        and then for a 32bit key if no 64bit key is present.
        """

        try:
            return Registry.ReadValue(_winreg.HKEY_CURRENT_USER, key_path, value_name, check_both_architectures)
        except Registry.Error as ex:
            if ex.errno == 2:  # Key/file not found
                return Registry.ReadValue(_winreg.HKEY_LOCAL_MACHINE, key_path, value_name, check_both_architectures)

            raise

    @staticmethod
    def ReadValueMachineAndUser(key_path, value_name, check_both_architectures=False):
        """Read the value value_name from the key key_path from Local Machine and
        then Current User if reading from Local Machine failed.

        If check_both_architectures is True, it will first check for a 64bit key
        and then for a 32bit key if no 64bit key is present.
        """

        try:
            return Registry.ReadValue(_winreg.HKEY_LOCAL_MACHINE, key_path, value_name, check_both_architectures)
        except Registry.Error as ex:
            if ex.errno == 2:  # Key/file not found
                return Registry.ReadValue(_winreg.HKEY_CURRENT_USER, key_path, value_name, check_both_architectures)

            raise
