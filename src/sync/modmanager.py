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

import multiprocessing
from multiprocessing import Queue
import os

from kivy.logger import Logger
import requests

from utils.process import Process
from utils.app import BaseApp
from sync.httpsyncer import HttpSyncer
from sync.torrentsyncer import TorrentSyncer
from sync.mod import Mod
from arma.arma import Arma, ArmaNotInstalled

def get_mod_descriptions(messagequeue):
    """
    helper function to get the moddescriptions from the server

    this function is ment be used threaded or multiprocesses, you have
    to pass in a queue
    """
    messagequeue.progress({'msg': 'Downloading mod descriptions'})
    url = 'https://gist.githubusercontent.com/Sighter/adbce21192d0413cfbad/raw/074c5227b54ca7cb2abce918f08ce4b6a8362f66/moddesc.json'
    res = requests.get(url, verify=False)
    data = None

    mods = []

    if res.status_code != 200:
        messagequeue.put({'action': 'moddescdownload', 'status': 'failed',
                          'progress': 0.0, 'kbpersec': 0.0,})
        return
    else:
        data = res.json()

        for md in data:
            mods.append(Mod.fromDict(md))

        messagequeue.progress({'msg': 'Downloading mod descriptions finished', 'mods': mods})

    return mods

class ModManager(object):
    """docstring for ModManager"""
    def __init__(self):
        super(ModManager, self).__init__()

    def _check_already_installed_with_six(self, mod):
        """returns true if mod is installed already with withsix, otherwise false"""

        # check user path
        install_path = Arma.get_user_path()
        mod_path = os.path.join(install_path, mod.name, '.synqinfo')

        if os.path.isfile(mod_path):
            return True

        # check system path
        install_path = Arma.get_installation_path()
        mod_path = os.path.join(install_path, mod.name, '.synqinfo')

        return os.path.isfile(mod_path)

    def prepare_and_check(self, messagequeue):
        """do everything which is needed to get all mods in sync"""

        # download mod descriptions first
        mod_list = get_mod_descriptions(messagequeue)

        # check if any oth the mods is installed with withSix
        messagequeue.progress({'msg': 'Checking mods'})
        for m in mod_list:
            try:
                r = self._check_already_installed_with_six(m)
            except ArmaNotInstalled:
                r = False
            if r:
                messagequeue.progress({'msg': 'Mod ' + m.name + ' already installed with withSix'})

        messagequeue.resolve({'msg': 'Checking mods finished'})


    def sync_all(self, messagequeue):

        # TODO: Sync via libtorrent
        # The following is just test code

        cba_mod = Mod(
            name='@CBA_A3',
            clientlocation='../tests/',
            synctype='http',
            downloadurl='http://dev.withsix.com/attachments/download/22231/CBA_A3_RC4.7z');

        cba_syncer = HttpSyncer(messagequeue, cba_mod)
        cba_syncer.sync()

        debussy_mod = Mod(
            name='@debussybattle',
            clientlocation=os.getcwd(),  # TODO: Change me
            synctype='torrent',
            downloadurl=BaseApp.resource_path('debussy.torrent'))

        debussy_syncer = TorrentSyncer(messagequeue, debussy_mod)
        debussy_syncer.sync()

        messagequeue.resolve({'msg': 'Downloading mods finished.'})

        return

if __name__ == '__main__':

    m = ModManager()
    m.sync_all(Queue())
