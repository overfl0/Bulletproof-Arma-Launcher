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

from kivy.logger import Logger
import requests

from utils.process import Process
from sync.httpsyncer import HttpSyncer

def get_mod_descriptions(messagequeue):
    """helper function to get the moddescriptions from the server"""
    url = 'https://gist.githubusercontent.com/Sighter/adbce21192d0413cfbad/raw/074c5227b54ca7cb2abce918f08ce4b6a8362f66/moddesc.json'
    res = requests.get(url)

    if res.status_code != 200:
        messagequeue.put({
            'action': 'moddescdownload',
            'status': 'failed',
            'progress': 0.0,
            'kbpersec': 0.0,})
        return
    else:
        data = res.json()

        messagequeue.put({
            'action': 'moddescdownload',
            'status': 'finished',
            'progress': 1.0,
            'kbpersec': 0.0,
            'data': data})
    return

class SubProcess(Process):
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
        loc = mod.clientlocation
        url = mod.downloadurl
        syncclass = None

        if mod.synctype == 'http':
            syncclass = HttpSyncer

        Logger.debug('ModManager: syncing mod:' + mod.name)

        self.current_queue = Queue()
        SubProcess(syncclass, self.current_queue, mod);

    def _check_already_installed_with_six(self, mod):
        pass

    def _get_arma_folders(self):
        pass

    def _get_remote_mod_list(self):
        pass

    def _get_syncer(self, type):
        """
        gets a syncer CLASS by type
        """
        if type == 'http':
            return HttpSyncer

        return None

    def sync_all(self, messagequeue):
        # download mod descriptions first
        messagequeue.put({
            'action': 'moddescdownload',
            'status': 'downloading',
            'progress': 0.3,
            'kbpersec': 0.0,})
        get_mod_descriptions(messagequeue)

    def query_status(self):
        if not self.current_queue.empty():
            progress = self.current_queue.get_nowait()
            return progress
        else:
            return None
