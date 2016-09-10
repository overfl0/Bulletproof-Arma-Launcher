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

# Allow relative imports when the script is run from the command line
if __name__ == "__main__":
    import site
    import os
    file_directory = os.path.dirname(os.path.realpath(__file__))
    site.addsitedir(os.path.abspath(os.path.join(file_directory, '..')))


import os
import subprocess

from kivy.logger import Logger
from utils import unicode_helpers
from utils.devmode import devmode
from utils.singleton import Singleton
from utils.registry import Registry

from . import SoftwareNotInstalled


# Exceptions:
class ArmaNotInstalled(SoftwareNotInstalled):
    pass


class SteamNotInstalled(SoftwareNotInstalled):
    pass


class Arma(object):
    __metaclass__ = Singleton
    __custom_path = None

    # Registry paths
    _arma_registry_path = r"software\bohemia interactive\arma 3"
    _arma_registry_path_alternate = r"software\Bohemia Interactive Studio\arma 3"
    _arma_expansions_registry_path = r"software\bohemia interactive\arma 3\expansions\arma 3"
    _user_document_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
    _steam_registry_path = r"Software\Valve\Steam"

    @staticmethod
    def get_custom_path():
        """Return a custom mod installation path set by the user.
        If no path has been set beforehand, returns None"""
        return Arma().__custom_path

    @staticmethod
    def set_custom_path(new_path):
        """Set a custom mod installation path.
        Note: The function does NOT convert the path to an absolute path."""
        Arma().__custom_path = new_path

    @staticmethod
    def get_installation_path():
        """Return the folder where Arma is installed.
        Raises ArmaNotInstalled if the required registry keys cannot be found."""

        if devmode.get_arma_path():
            return devmode.get_arma_path()

        path = None
        try:
            path = Registry.ReadValueUserAndMachine(Arma._arma_registry_path, 'main', check_both_architectures=True)

        except Registry.Error:
            try:
                path = Registry.ReadValueUserAndMachine(Arma._arma_registry_path_alternate, 'main', check_both_architectures=True)

            except Registry.Error:
                raise ArmaNotInstalled()

        return path

    @staticmethod
    def get_user_directory():

        try:
            user_docs = Registry.ReadValueCurrentUser(Arma._user_document_path, 'Personal')
        except Registry.Error:
            raise ArmaNotInstalled()

        return user_docs

    @staticmethod
    def get_executable_path(battleye=True):
        """Return path to the arma executable.
        The battleye variable allows to run the battleye-enhanced version of the game.

        Raises ArmaNotInstalled if Arma is not installed."""

        if battleye:
            executable = "arma3battleye.exe"
        else:
            executable = "arma3.exe"

        return os.path.join(Arma.get_installation_path(), executable)

    @staticmethod
    def get_steam_exe_path():
        """Return the path to the steam executable.

        Raises SteamNotInstalled if steam is not installed."""

        if devmode.get_steam_executable():
            return devmode.get_steam_executable()

        try:
            # Optionally, there is also SteamPath
            return Registry.ReadValueUserAndMachine(Arma._steam_registry_path, 'SteamExe', check_both_architectures=True)  # SteamPath

        except Registry.Error:
            raise SteamNotInstalled()

    @staticmethod
    def run_game(mod_list=None, profile_name=None, custom_args=None, battleye=True,
                 ip=None, port=None, password=None):
        """Run the game in a separate process.

        All mods in mod_list are applied as command line parameters. The profile_name is also used.
        Custom_args are appended as is and special care must be taken when using spaces.
        The battleye variable allows to run the battleye-enhanced version of the game.

        Raises ArmaNotInstalled if Arma is not installed.
        Raises SteamNotInstalled if Steam is not installed.
        Raises OSError if running the executable fails."""

        # http://feedback.arma3.com/view.php?id=23435
        # Correct launching method when steam is turned off:
        # steam.exe -applaunch 107410 -usebe -nolauncher -connect=IP -port=PORT -mod=<modparameters>

        steam_exe_path = Arma.get_steam_exe_path()
        game_args = [steam_exe_path, '-applaunch', '107410']

        if battleye:
            game_args.append('-usebe')

        game_args.extend(['-nosplash', '-skipIntro', '-nolauncher'])

        if mod_list:
            modlist_argument = '-mod=' + ';'.join(mod_list)
            game_args.extend([modlist_argument])

        if profile_name:
            game_args.extend(['-name=' + profile_name])

        if ip:
            game_args.extend(['-connect=' + ip])

        if port:
            game_args.extend(['-port=' + port])

        if password:
            game_args.extend(['-password=' + password])

        if custom_args:
            game_args.extend(custom_args)

        Logger.info('Arma: game args: [{}]'.format(', '.join(game_args)))
        popen_object = subprocess.Popen(unicode_helpers.u_to_fs_list(game_args))  # May raise OSError

        return popen_object

if __name__ == "__main__":
    pass
