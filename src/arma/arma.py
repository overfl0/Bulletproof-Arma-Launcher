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

# Allow relative imports when the script is run from the command line
if __name__ == "__main__":
    import site
    import os
    file_directory = os.path.dirname(os.path.realpath(__file__))
    site.addsitedir(os.path.abspath(os.path.join(file_directory, '..')))


import os
import subprocess

from utils.singleton import Singleton
from utils.registry import Registry

# Exceptions:
class ArmaNotInstalled(Exception):
    pass


class Arma(object):
    __metaclass__ = Singleton
    __custom_path = None

    # Registry paths
    _arma_registry_path = r"software\bohemia interactive\arma 3"
    _arma_expansions_registry_path = r"software\bohemia interactive\arma 3\expansions\arma 3"
    _user_document_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"

    @staticmethod
    def get_custom_path():
        """Returns a custom mod installation path set by the user.
        If no path has been set beforehand, returns None"""
        return Arma().__custom_path

    @staticmethod
    def set_custom_path(new_path):
        """Set a custom mod installation path.
        Note: The function does NOT convert the path to an absolute path."""
        Arma().__custom_path = new_path

    @staticmethod
    def get_installation_path():
        """Returns the folder where Arma is installed.
        Raises ArmaNotInstalled if the required registry keys cannot be found."""

        path = None
        try:
            path = Registry.ReadValueMachine(Arma._arma_registry_path, 'main')
        except Registry.Error:
            raise ArmaNotInstalled()

        return path

    @staticmethod
    def get_user_path():

        path = None
        try:
            user_docs = Registry.ReadValueCurrentUser(Arma._user_document_path, 'Personal')
            path = os.path.join(user_docs, 'Arma 3')
        except Registry.Error:
            raise ArmaNotInstalled()

        return path

    @staticmethod
    def get_executable_path():
        """Returns path to the arma executable.
        Raises ArmaNotInstalled if Arma is not installed."""
        return os.path.join(Arma.get_installation_path(), "arma3.exe")

    @staticmethod
    def run_game(mod_list=None, profile_name=None, custom_args=None):
        """Run the game in a separate process.

        All mods in mod_list are applied as command line parameters. The profile_name is also used.
        Custom_args are appended as is and special care must be taken when using spaces.
        Raises ArmaNotInstalled if Arma is not installed.
        Raises OSError if running the executable fails."""

        arma_path = Arma.get_executable_path()
        game_args = [arma_path, '-nosplash', '-skipIntro']

        if mod_list:
            modlist_argument = '-mod=' + ';'.join(mod_list)
            game_args.extend([modlist_argument])

        if profile_name:
            game_args.extend(['-name=' + profile_name])

        if custom_args:
            game_args.extend(custom_args)

        popen_object = subprocess.Popen(game_args)  # May raise OSError


if __name__ == "__main__":
    pass
