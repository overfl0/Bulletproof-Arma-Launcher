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

# Allow relative imports when the script is run from the command line
if __name__ == "__main__":
    import site
    import os
    file_directory = os.path.dirname(os.path.realpath(__file__))
    site.addsitedir(os.path.abspath(os.path.join(file_directory, '..')))


import os
import platform
import urllib

from kivy.logger import Logger
from utils.devmode import devmode
from utils import process_launcher
from utils.registry import Registry
from utils.system_processes import program_running

from . import SoftwareNotInstalled


# Exceptions:
class ArmaNotInstalled(SoftwareNotInstalled):
    pass


class SteamNotInstalled(SoftwareNotInstalled):
    pass


class Arma(object):
    # Registry paths
    _arma_registry_path = r"software\bohemia interactive\arma 3"
    _arma_registry_path_alternate = r"software\Bohemia Interactive Studio\arma 3"
    _arma_expansions_registry_path = r"software\bohemia interactive\arma 3\expansions\arma 3"
    _user_document_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
    _steam_registry_path = r"Software\Valve\Steam"
    _profile_directory_name = "Arma 3 - Other Profiles"

    @staticmethod
    def _is_os_64bit():
        return platform.machine().endswith('64')

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
    def get_player_profiles():
        """Retrieve available player profiles.
        The profiles are stored in '~/Documents/Arma 3 - Other Profiles' (on
        Windows) and are in utf-8 that is then urlencoded.
        """

        profiles = []
        profiles_directory = os.path.join(Arma.get_user_directory(), Arma._profile_directory_name)

        try:
            arma_profiles_dir_contents = os.listdir(profiles_directory)

        except OSError:
            return profiles

        for filename in arma_profiles_dir_contents:
            if not os.path.isdir(os.path.join(profiles_directory, filename)):
                continue

            try:
                # We need to convert the unquoted unicode python string to bytes
                # so we use encode('latin-1') for that.
                # Any error here indicates that this is not a valid profile
                profile_name = urllib.unquote(filename).encode('latin-1').decode('utf-8')

            except:
                Logger.error('Arma: get_player_profiles: Error when converting {}'.format(repr(filename)))
                continue

            profiles.append(profile_name)

        return profiles

    @staticmethod
    def get_executable(force_32bit=False, force_64bit=False):
        """Return path to the arma executable.

        If neither 32bit nor 64bit are forced, the executable is selected based
        on the operating system running right now.

        Raises ArmaNotInstalled if Arma is not installed."""

        if force_64bit:
            executable = "arma3_x64.exe"
        elif force_32bit:
            executable = "arma3.exe"
        else:
            if Arma._is_os_64bit():
                executable = "arma3_x64.exe"
            else:
                executable = "arma3.exe"

        return executable

    @staticmethod
    def get_launcher_path():
        """Return the path to the arma launcher executable."""

        return os.path.join(Arma.get_installation_path(), 'arma3launcher.exe')

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
    def run_arma3_launcher():
        """Run the original arma 3 launcher."""
        steam_exe_path = Arma.get_steam_exe_path()  # May raise SteamNotInstalled!
        game_args = [steam_exe_path, '-applaunch', '107410']

        Logger.info('Arma: game args: [{}]'.format(', '.join(game_args)))
        popen_object = process_launcher.run(game_args)  # May raise OSError

        return popen_object

    @staticmethod
    def get_args_to_execute(battleye=True, force_32bit=False, force_64bit=False):
        """Return a list containing arguments needed to start the game.
        This list can the further be extended with additional arguments but
        this one will be the absolute minimum in order to start anything.

        The battleye variable allows to run the battleye-enhanced version of the game.

        Raises ArmaNotInstalled if Arma is not installed.
        """

        # If steam is running, run Arma.exe directly (some users have had this
        # strange bug that arma would not launch if Steam.exe was already running
        # Even though running the exact same command from cmd.exe worked fine!
        if program_running('Steam.exe'):
            executable = Arma.get_executable(force_32bit=force_32bit,
                                             force_64bit=force_64bit)

            if battleye:
                game_args = ['2', '1', '0', '-exe', executable]
                executable = "arma3battleye.exe"

            else:
                game_args = []

            executable_path = os.path.join(Arma.get_installation_path(), executable)
            return [executable_path] + game_args

        else:
            # Steam is not running right now so run the game through steam
            # http://feedback.arma3.com/view.php?id=23435
            # Correct launching method when steam is turned off:
            # steam.exe -applaunch 107410 -usebe -nolauncher -connect=IP -port=PORT -mod=<modparameters>

            steam_exe_path = Arma.get_steam_exe_path()
            game_args = [steam_exe_path, '-applaunch', '107410', '-nolauncher']

            if battleye:
                game_args.append('-usebe')

        return game_args

    @staticmethod
    def run_game(mod_list=None, profile_name=None, custom_args=None, battleye=True,
                 ip=None, port=None, password=None, mission_file=None,
                 force_32bit=False, force_64bit=False):
        """Run the game in a separate process.

        All mods in mod_list are applied as command line parameters. The profile_name is also used.
        Custom_args are appended as is and special care must be taken when using spaces.
        The battleye variable allows to run the battleye-enhanced version of the game.

        Raises ArmaNotInstalled if Arma is not installed.
        Raises SteamNotInstalled if Steam is not installed.
        Raises OSError if running the executable fails."""

        game_args = Arma.get_args_to_execute(battleye=battleye,
                                             force_32bit=force_32bit,
                                             force_64bit=force_64bit)

        game_args.extend(['-nosplash', '-skipIntro'])

        if mod_list:
            modlist_argument = '-mod=' + ';'.join(mod_list)
            game_args.extend([modlist_argument])

        if profile_name:
            game_args.extend(['-name=' + profile_name])

        if ip:
            if not mission_file:
                game_args.extend(['-connect=' + ip])
            else:
                Logger.info('Arma: Mission file parameter present. Not connecting to server!')

        if port:
            game_args.extend(['-port=' + port])

        if password:
            game_args.extend(['-password=' + password])

        if custom_args:
            game_args.extend(custom_args)

        if mission_file:
            game_args.append(mission_file)

        Logger.info('Arma: game args: [{}]'.format(', '.join(game_args)))
        popen_object = process_launcher.run(game_args)  # May raise OSError

        return popen_object

if __name__ == "__main__":
    pass
