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

import errno
import os
import shutil
import subprocess
import textwrap

from utils.paths import u_to_fs
from third_party import SoftwareNotInstalled
from utils.context import ignore_nosuchfile_exception
from utils.devmode import devmode
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
    """Run all the registry checks. If any of them fails, raises TeamspeakNotInstalled()."""

    print get_executable_path()
    print get_addon_installer_path()
    print get_install_location()
    print get_config_location()


def create_package_ini_file(path, name, author, version, platforms, description):
    """Create a package.ini file at <path> for a future ts3_plugin file."""
    package_ini = textwrap.dedent("""Name = {}
                                     Type = Plugin
                                     Author = {}
                                     Version = {}
                                     Platforms = {}
                                     Description = "{}"
    """).format(name, author, version, ', '.join(platforms), description)
    package_ini_path = os.path.join(path, 'package.ini')

    with file(package_ini_path, 'w') as f:
        f.write(package_ini)


def create_teamspeak_package(path, name, author, version, platforms, description):
    """Create a teamspeak ts3_plugin file from files in <path>.
    The created file will be called tfr.ts3_plugin.
    """

    package_ini_path = os.path.join(path, 'package.ini')
    zip_path_no_extension = os.path.join(path, 'tfr')
    zip_path = zip_path_no_extension + '.zip'
    ts3_plugin_path = os.path.join(path, 'tfr.ts3_plugin')

    try:
        create_package_ini_file(path=path, name=name, author=author,
                                version=version, platforms=platforms,
                                description=description)

        # Ensure the previously generated files will not get included in the package
        with ignore_nosuchfile_exception():
            os.unlink(zip_path)

        with ignore_nosuchfile_exception():
            os.unlink(ts3_plugin_path)

        # Create a zip file containing plugins and package.ini
        shutil.make_archive(zip_path_no_extension, 'zip', path)
        os.rename(zip_path, ts3_plugin_path)

        return ts3_plugin_path

    finally:
        with ignore_nosuchfile_exception():
            os.unlink(package_ini_path)

        with ignore_nosuchfile_exception():
            os.unlink(zip_path)


def install_unpackaged_plugin(path):
    """Package a plugin located at <path> to a ts3_plugin file and then install it.
    The created ts3_plugin file will be left in place because we cannot know when
    the installer terminates, yet.
    """

    version = 'Unknown'

    tfr_package = create_teamspeak_package(
        path,
        name='Task Force Arma 3 Radio',
        author='[TF]Nkey',
        version=version,
        platforms=['win32', 'win64'],
        description='Task Force Arrowhead Radio.\nPlugin packaged automatically by TacBF launcher team.'
    )

    addon_installer = get_addon_installer_path()
    args = u_to_fs([addon_installer, tfr_package])
    subprocess.call(args)
    # TODO: Wait for this to finish in a separate thread (use promises)
