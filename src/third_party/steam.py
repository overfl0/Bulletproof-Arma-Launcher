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

# Allow relative imports when the script is run from the command line
if __name__ == "__main__":
    import site
    import os
    file_directory = os.path.dirname(os.path.realpath(__file__))
    site.addsitedir(os.path.abspath(os.path.join(file_directory, '..')))


from utils.devmode import devmode
from utils.registry import Registry

from . import SoftwareNotInstalled


class SteamNotInstalled(SoftwareNotInstalled):
    pass


_steam_registry_path = r"Software\Valve\Steam"


def get_steam_exe_path():
    """Return the path to the steam executable.

    Raises SteamNotInstalled if steam is not installed."""

    if devmode.get_steam_executable():
        return devmode.get_steam_executable()

    try:
        # Optionally, there is also SteamPath
        return Registry.ReadValueUserAndMachine(_steam_registry_path, 'SteamExe', check_both_architectures=True)  # SteamPath

    except Registry.Error:
        raise SteamNotInstalled()
