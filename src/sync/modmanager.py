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
from sync.httpsyncer import HttpSyncer
from sync.mod import Mod
from arma.arma import Arma

def get_mod_descriptions(messagequeue):
    """
    helper function to get the moddescriptions from the server

    this function is ment be used threaded or multiprocesses, you have
    to pass in a queue
    """
    url = 'https://gist.githubusercontent.com/Sighter/adbce21192d0413cfbad/raw/074c5227b54ca7cb2abce918f08ce4b6a8362f66/moddesc.json'
    res = requests.get(url)
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

        messagequeue.put({'action': 'moddescdownload', 'status': 'finished',
            'progress': 1.0, 'kbpersec': 0.0, 'data': mods})

    return mods

class SubProcess(Process):
    # TODO think about removing this
    def __init__(self, syncclass, resultQueue, mod):
        self.resultQueue = resultQueue
        self.syncclass = syncclass
        self.mod = mod

        multiprocessing.Process.__init__(self)
        self.start()

    def run(self):
        syncer = self.syncclass(self.resultQueue, self.mod)
        syncer.sync()

class ModManager(object):
    """docstring for ModManager"""
    def __init__(self):
        super(ModManager, self).__init__()

    def _sync_single_mod(self, mod):

        # TODO do not thread of here

        loc = mod.clientlocation
        url = mod.downloadurl
        syncclass = None

        if mod.synctype == 'http':
            syncclass = HttpSyncer

        Logger.debug('ModManager: syncing mod:' + mod.name)

        self.current_queue = Queue()
        SubProcess(syncclass, self.current_queue, mod);

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

    def _get_syncer(self, type):
        """
        gets a syncer CLASS by type
        """
        if type == 'http':
            return HttpSyncer

        return None

    def sync_all(self, messagequeue):
        """do everything which is needed to get all mods in sync"""

        # download mod descriptions first
        messagequeue.put({
            'action': 'moddescdownload', 'status': 'inprogress',
            'progress': 0.3, 'kbpersec': 0.0,})
        mod_list = get_mod_descriptions(messagequeue)

        # check if any oth the mods is installed with withSix
        for m in mod_list:
            r = self._check_already_installed_with_six(m)
            if r:
                messagequeue.put({
                    'action': 'checkmods', 'status': 'inprogress',
                    'progress': 0.3, 'kbpersec': 0.0,
                    'msg': 'Mod ' + m.name + ' already installed with withSix'})

        messagequeue.put({
            'action': 'checkmods', 'status': 'finished',
            'progress': 0.1, 'kbpersec': 0.0})

        # TODO: Sync via libtorrent

        return

    def query_status(self):
        if not self.current_queue.empty():
            progress = self.current_queue.get_nowait()
            return progress
        else:
            return None

if __name__ == '__main__':

    m = ModManager()
    m.sync_all(Queue())
