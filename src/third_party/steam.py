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

import os
import re

from kivy.logger import Logger
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


# path = 'C:\\Program Files (x86)\\Steam\\steamapps\\libraryfolders.vdf'
# base_steam_path = 'C:\\Program Files (x86)\\Steam'
# library_template = '{library}\steamapps\common\{game}\steam_appid.txt'

"""
Example of a libraryfolders.vdf:
Note: Strings seem to be utf-8 encoded

"LibraryFolders"
{
    "TimeNextStatsReport"        "1494451429"
    "ContentStatsID"        "5476921788564740081"
    "1"        "D:\\Steam"
    "2"        "E:\\Zolw"
}
"""

def find_steam_libraries():
    """Quick and shitty vdf parsing in order to find steam libraries locations."""

    # Matching:     "5"     "D:\\Steam"
    pattern = re.compile(""" \s*  "(\d+)"  \s+  "([^"]+)"  .* """, re.VERBOSE)

    base_steam_path = os.path.dirname(get_steam_exe_path())
    libraries = [base_steam_path]
    Logger.info('Steam: Adding base library: {}'.format(base_steam_path))
    path = os.path.join(base_steam_path, 'steamapps', 'libraryfolders.vdf')

    try:
        with open(path, b'rb') as f:
            lines = f.readlines()

            for line in lines:
                match = pattern.match(line)

                if match:
                    library_str = match.group(2)
                    try:
                        library_decoded = library_str.decode('utf-8').replace('\\\\', '\\')

                    except UnicodeDecodeError as ex:
                        Logger.error('Steam: Error while decoding the line: {}:{}'.format(repr(line), ex))
                        continue

                    libraries.append(library_decoded)
                    Logger.info('Steam: Adding library: {}'.format(library_decoded))

            return libraries

    except Exception as ex:
        Logger.error('Steam: Could not read library file {}: {}'.format(path, ex))
        return libraries


if __name__ == '__main__':
    libraries = find_steam_libraries()

    for library in libraries:
        tested_path = os.path.join(library, 'steamapps', 'common', 'Arma 3', 'Arma3.exe')
        if os.path.isfile(tested_path):
            print 'Found in: {}'.format(tested_path)
