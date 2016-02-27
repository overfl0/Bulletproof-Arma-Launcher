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

import textwrap

from third_party import teamspeak
from third_party.arma import Arma, ArmaNotInstalled, SteamNotInstalled
from view.messagebox import MessageBox


def check_requirements(verbose=True):
    """Check if all the required third party programs are installed in the system.
    Return True if the check passed.
    If verbose == true, show a message box in case of a failed check.
    """

    # TODO: move me to a better place
    try:
        teamspeak.check_installed()
    except teamspeak.TeamspeakNotInstalled:
        if verbose:
            message = textwrap.dedent('''
                Teamspeak does not seem to be installed.
                Having Teamspeak is required in order to play Tactical Battlefield.

                [ref=https://www.teamspeak.com/downloads][color=3572b0]Get Teamspeak here.[/color][/ref]

                Install Teamspeak and restart the launcher.
                ''')
            box = MessageBox(message, title='Teamspeak required!', markup=True)
            box.chain_open()

        return False

    try:
        Arma.get_installation_path()
    except ArmaNotInstalled:
        if verbose:
            message = textwrap.dedent('''
                Arma 3 does not seem to be installed.

                Having Arma 3 is required in order to play Tactical Battlefield.
                ''')
            box = MessageBox(message, title='Arma 3 required!', markup=True)
            box.chain_open()

        return False

    try:
        Arma.get_steam_exe_path()
    except SteamNotInstalled:
        if verbose:
            message = textwrap.dedent('''
                Steam does not seem to be installed.
                Having Steam is required in order to play Tactical Battlefield.

                [ref=http://store.steampowered.com/about/][color=3572b0]Get Steam here.[/color][/ref]

                Install Steam and restart the launcher.
                ''')
            box = MessageBox(message, title='Steam required!', markup=True)
            box.chain_open()

        return False

    return True
