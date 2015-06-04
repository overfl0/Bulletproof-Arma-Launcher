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
import json
import traceback
import sys

from datetime import datetime

import kivy
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


def get_mod_descriptions(para):
    """
    helper function to get the moddescriptions from the server

    this function is ment be used threaded or multiprocesses, you have
    to pass in a queue
    """
    downloadurlPrefix = 'http://91.121.120.221/tacbf/updater/torrents/'


    para.progress({'msg': 'Downloading mod descriptions'})
    url = 'http://91.121.120.221/tacbf/updater/metadata.json'
    #url = 'https://gist.githubusercontent.com/Sighter/cd769854a3adeec8908e/raw/a187f49eac56136a0555da8e2f1a86c3cc694d27/metadata.json'
    res = requests.get(url, verify=False)
    data = None

    mods = []

    if res.status_code != 200:
        para.reject({'msg': '{}\n{}\n\n{}'.format(
            'Moddescriptions could not be received from the server',
            'Status Code: ' + str(res.status_code), res.text)})
    else:
        try:
            data = res.json()
        except ValueError as e:
            Logger.error('ModManager: Failed to parse moddescription json!')
            stacktrace = "".join(traceback.format_exception(*sys.exc_info()))
            para.reject({'msg': '{}\n\n{}'.format(
                'Mod descriptions could not be parsed', stacktrace)})

        # Temporary! Ensure alpha version is correct
        if data.get('alpha') != "1":
            error_message = 'This launcher is out of date! You won\'t be able do download mods until you update to the latest version!'
            Logger.error(error_message)
            para.reject({'msg': error_message})
            return []

        for md in data['mods']:

            # parse timestamp
            tsstr = md.get('torrent-timestamp')
            md['torrent-timestamp'] = parse_timestamp(tsstr)
            md['downloadurl'] = "{}{}-{}.torrent".format(downloadurlPrefix,
                md['foldername'], tsstr)

            mods.append(Mod.fromDict(md))

            Logger.debug('ModManager: Got mod description: ' + repr(md))

        para.progress({'msg': 'Downloading mod descriptions finished', 'mods': mods})

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
    if mod_list is None:  # Alpha version addition
        return

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

def _sync_all(messagequeue, launcher_moddir, mods):
    # WARNING: This methods gets called in a diffrent process

    # TODO: Sync via libtorrent
    # The following is just test code

    # cba_mod = Mod(
    #     foldername='@CBA_A3',
    #     clientlocation=launcher_moddir,
    #     synctype='http',
    #     downloadurl='http://dev.withsix.com/attachments/download/22231/CBA_A3_RC4.7z');
    #
    # cba_syncer = HttpSyncer(messagequeue, cba_mod)
    # cba_syncer.sync()

    # debussy_mod = Mod(
    #     foldername='@debussybattle',  # The mod name MUST match directory name!
    #     clientlocation=launcher_moddir,
    #     synctype='torrent',
    #     downloadurl='file://' + BaseApp.resource_path('debussy.torrent'))

    for m in mods:
        m.clientlocation = launcher_moddir

        syncer = TorrentSyncer(messagequeue, m)
        # Alpha version: do not force sync. Let's try to do this the right way.
        # Forcing should be at an explicit request of the user
        syncer.sync(force_sync=False)  # Use force_sync to force full recheck of all the files' checksums

    messagequeue.resolve({'msg': 'Downloading mods finished.'})

    return

class ModManager(object):
    """docstring for ModManager"""
    def __init__(self):
        super(ModManager, self).__init__()
        self.para = None
        self.sync_para = None
        self.mods = None
        self.settings = kivy.app.App.get_running_app().settings

    def prepare_and_check(self):
        self.para = Para(_prepare_and_check, (), 'checkmods')
        self.para.then(self.on_prepare_and_check_resolve, None, None)
        self.para.run()
        return self.para

    def sync_all(self):
        self.sync_para = Para(_sync_all,
            (self.settings.get_launcher_moddir(), self.mods), 'sync')
        self.sync_para.run()
        return self.sync_para

    def on_prepare_and_check_resolve(self, data):
        Logger.info('ModManager: Got mods ' + repr(data['mods']))
        self.mods = data['mods']


if __name__ == '__main__':
    pass
