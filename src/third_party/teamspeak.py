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

from utils.devmode import devmode
from third_party import SoftwareNotInstalled
from utils.registry import Registry

class TeamspeakNotInstalled(SoftwareNotInstalled):
    pass


def _parse_windows_cmdline(cmdline):
    """Parse command line from windows with its bizarre quoting mechanism."""

    import ctypes
    reload(ctypes)  # This fixes problems with ipython

    size = ctypes.c_int()
    ptr = ctypes.windll.shell32.CommandLineToArgvW(cmdline, ctypes.byref(size))
    ref = ctypes.c_wchar_p * size.value
    raw = ref.from_address(ptr)
    args = [arg for arg in raw]
    ctypes.windll.kernel32.LocalFree(ptr)
    
    return args
    

def get_executable_path():
    """Return the path of the teamspeak executable."""

    if devmode.get_ts_executable():
        return devmode.get_ts_executable()

    try:
        key = 'SOFTWARE\\classes\\ts3file\\shell\\open\\command'
        reg_val = Registry.ReadValueUserAndMachine(key, '', False)
        args = _parse_windows_cmdline(reg_val)

        return args[0]

    except Registry.Error:
        raise TeamspeakNotInstalled()

    except IndexError:
        raise


def get_addon_installer_path():
    """Return the path of the addon installer for teamspeak."""

    if devmode.get_ts_addon_installer():
        return devmode.get_ts_addon_installer()

    try:
        key = 'SOFTWARE\\Classes\\ts3addon\\shell\\open\\command'
        reg_val = Registry.ReadValueUserAndMachine(key, '', False)
        args = _parse_windows_cmdline(reg_val)

        return args[0]

    except Registry.Error:
        raise TeamspeakNotInstalled()

    except IndexError:
        raise


def get_install_location():
    """Return the path to where teamspeak executables are installed."""

    if devmode.get_ts_install_location():
        return devmode.get_ts_install_location()

    try:
        key = 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\TeamSpeak 3 Client'
        reg_val = Registry.ReadValueUserAndMachine(key, 'InstallLocation', True)
        return reg_val

    except Registry.Error:
        raise TeamspeakNotInstalled()


def get_config_location():
    """Return the value meaning where the user configuration is stored.
      0 - C:/Users/<username>/AppData/Roaming/TS3Client
      1 - Installation folder (get_install_location()/config).
    The actual directory may not exist until the user actually launches Teamspeak!
    """

    if devmode.get_ts_config_location():
        return devmode.get_ts_config_location()

    try:
        key = 'SOFTWARE\\TeamSpeak 3 Client'
        reg_val = Registry.ReadValueUserAndMachine(key, 'ConfigLocation', True)
        return reg_val

    except Registry.Error:
        raise TeamspeakNotInstalled()


def check_installed():
    """Runs all the registry checks. If any of them fails, raises TeamspeakNotInstalled()."""

    print get_executable_path()
    print get_addon_installer_path()
    print get_install_location()
    print get_config_location()


package_ini = """
Name = Task Force Arma 3 Radio
Type = Plugin
Author = [TF]Nkey
Version = Unknown
Platforms = win32, win64
Description = "Task Force Arrowhead Radio.\nPlugin automatically packaged by the TacBF team."
"""
