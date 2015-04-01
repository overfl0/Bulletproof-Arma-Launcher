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

from datetime import datetime

from kivy.logger import Logger
import requests

from utils.process import Process
from utils.process import Para
from utils.app import BaseApp
from sync.httpsyncer import HttpSyncer
from sync.torrentsyncer import TorrentSyncer
from sync.mod import Mod
from arma.arma import Arma, ArmaNotInstalled

def parse_timestamp(ts):
    """
    parse a time stamp to like this
    YYYY-MM-DD_Epoch

    we parse Epoch in utc time. After that make sure to use it like utc
    """
    s = ts.split('_')
    stamp = s[1]
    return datetime.utcfromtimestamp(float(stamp))


def get_mod_descriptions(messagequeue):
    """
    helper function to get the moddescriptions from the server

    this function is ment be used threaded or multiprocesses, you have
    to pass in a queue
    """
    messagequeue.progress({'msg': 'Downloading mod descriptions'})
    url = 'https://gist.githubusercontent.com/Sighter/cd769854a3adeec8908e/raw/a187f49eac56136a0555da8e2f1a86c3cc694d27/metadata.json'
    res = requests.get(url, verify=False)
    data = None

    mods = []

    if res.status_code != 200:
        messagequeue.put({'action': 'moddescdownload', 'status': 'failed',
                          'progress': 0.0, 'kbpersec': 0.0,})
        return
    else:
        data = res.json()

        for md in data['mods']:

            # parse timestamp
            tsstr = md.get('torrent-timestamp')
            md['torrent-timestamp'] = parse_timestamp(tsstr)

            mods.append(Mod.fromDict(md))

        messagequeue.progress({'msg': 'Downloading mod descriptions finished', 'mods': mods})

    return mods


def _check_already_installed_with_six(mod):
    """returns true if mod is installed already with withsix, otherwise false"""

    # check user path
    install_path = Arma.get_user_path()
    mod_path = os.path.join(install_path, mod.foldername, '.synqinfo')

    if os.path.isfile(mod_path):
        return True

    # check system path
    install_path = Arma.get_installation_path()
    mod_path = os.path.join(install_path, mod.foldername, '.synqinfo')

    return os.path.isfile(mod_path)


def _prepare_and_check(messagequeue):
    # WARNING: This methods gets called in a diffrent process
    #          self is not what you think it is

    # download mod descriptions first
    mod_list = get_mod_descriptions(messagequeue)

    # check if any oth the mods is installed with withSix
    messagequeue.progress({'msg': 'Checking mods'})
    for m in mod_list:
        try:
            r = _check_already_installed_with_six(m)
        except ArmaNotInstalled:
            r = False
        if r:
            messagequeue.progress({'msg': 'Mod ' + m.foldername + ' already installed with withSix'})

    messagequeue.resolve({'msg': 'Checking mods finished', 'mods': mod_list})

def _sync_all(messagequeue):
    # WARNING: This methods gets called in a diffrent process

    # TODO: Sync via libtorrent
    # The following is just test code

    cba_mod = Mod(
        foldername='@CBA_A3',
        clientlocation='../tests/',
        synctype='http',
        downloadurl='http://dev.withsix.com/attachments/download/22231/CBA_A3_RC4.7z');

    cba_syncer = HttpSyncer(messagequeue, cba_mod)
    cba_syncer.sync()

    debussy_mod = Mod(
        foldername='@debussybattle',
        clientlocation=os.getcwd(),  # TODO: Change me
        synctype='torrent',
        downloadurl=BaseApp.resource_path('debussy.torrent'))

    debussy_syncer = TorrentSyncer(messagequeue, debussy_mod)
    debussy_syncer.sync()

    messagequeue.resolve({'msg': 'Downloading mods finished.'})

    return

class ModManager(object):
    """docstring for ModManager"""
    def __init__(self):
        super(ModManager, self).__init__()
        self.para = None
        self.sync_para = None

    def prepare_and_check(self):
        self.para = Para(_prepare_and_check, (), 'checkmods')
        self.para.run()
        return self.para

    def sync_all(self):
        self.sync_para = Para(_sync_all, (), 'sync')
        self.sync_para.run()
        return self.sync_para

if __name__ == '__main__':
    pass
