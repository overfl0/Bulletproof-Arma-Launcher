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

import multiprocessing
from multiprocessing import Queue
import os
import json
import sys

from datetime import datetime

import kivy
from kivy.logger import Logger
import requests

from third_party.arma import Arma, SoftwareNotInstalled
from utils.devmode import devmode
from utils.app import BaseApp
from utils.primitive_git import get_git_sha1_auto
from utils.process import Process
from utils.process import Para
from utils.testtools_compat import _format_exc_info
from sync.httpsyncer import HttpSyncer
from sync.mod import Mod
from sync.torrentsyncer import TorrentSyncer


def parse_timestamp(ts):
    """
    parse a time stamp to like this
    YYYY-MM-DD_Epoch

    we parse Epoch in utc time. After that make sure to use it like utc
    """
    s = ts.split('_')
    stamp = s[1]
    return datetime.utcfromtimestamp(float(stamp))


def requests_get_or_reject(para, domain, *args, **kwargs):
    """
    Helper function that adds our error handling to requests.get.
    Feel free to refactor it.
    """

    if not domain:
        domain = "the domain"

    try:
        res = requests.get(*args, **kwargs)
    except requests.exceptions.ConnectionError as ex:
        try:
            reason_errno = ex.message.reason.errno
            if reason_errno == 11004:
                para.reject({'msg': 'Could not resolve {}. Check your DNS settings.'.format(domain)})
        except:
            para.reject({'msg': 'Could not connect to the metadata server.'})

        para.reject({'msg': 'Could not connect to the metadata server.'})

    except requests.exceptions.Timeout:
        para.reject({'msg': 'The server timed out while downloading metadata information from the server.'})

    except requests.exceptions.RequestException as ex:
        para.reject({'msg': 'Could not download metadata information from the server.'})

    return res


def get_mod_descriptions(para, launcher_moddir):
    """
    helper function to get the moddescriptions from the server

    this function is ment be used threaded or multiprocesses, you have
    to pass in a queue
    """
    downloadurlPrefix = 'http://launcher.tacbf.com/tacbf/updater/torrents/'


    para.progress({'msg': 'Downloading mod descriptions'})
    domain = 'launcher.tacbf.com'
    url = 'http://{}/tacbf/updater/metadata.json'.format(domain)
    data = None
    res = requests_get_or_reject(para, domain, url, verify=False, timeout=10)

    mods = []

    if res.status_code != 200:
        para.reject({'msg': '{}\n{}\n\n{}'.format(
            'Mods descriptions could not be received from the server',
            'Status Code: ' + unicode(res.status_code), res.text)})
    else:
        try:
            data = res.json()
        except ValueError as e:
            Logger.error('ModManager: Failed to parse mods descriptions json!')
            stacktrace = "".join(_format_exc_info(*sys.exc_info()))
            para.reject({'msg': '{}\n\n{}'.format(
                'Mods descriptions could not be parsed', stacktrace)})

        # Temporary! Ensure alpha version is correct
        if data.get('alpha') not in ("2", "3", "4"):
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

            mod = Mod.fromDict(md)
            mod.clientlocation = launcher_moddir
            mods.append(mod)

            Logger.debug('ModManager: Got mods descriptions: ' + repr(md))

        para.progress({'msg': 'Downloading mods descriptions finished', 'mods': mods})

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


def _prepare_and_check(messagequeue, launcher_moddir):
    # WARNING: This methods gets called in a different process

    # download mod descriptions first
    mod_list = get_mod_descriptions(messagequeue, launcher_moddir)

    # Debug mode: decrease the number of mods to download
    mods_filter = devmode.get_mods_filter()
    if mods_filter:
        # Keep only the mods with names starting with any of the giver filters
        mod_list = [mod for mod in mod_list if any(mod.name.startswith(prefix) for prefix in mods_filter)]

    # check if any oth the mods is installed with withSix
    messagequeue.progress({'msg': 'Checking mods'})
    for m in mod_list:
        try:
            r = _check_already_installed_with_six(m)
        except SoftwareNotInstalled:
            r = False
        if r:
            messagequeue.progress({'msg': 'Mod ' + m.foldername + ' already installed with withSix'})

        # TODO: Change this to a static function
        syncer = TorrentSyncer(messagequeue, m)
        m.up_to_date = syncer.is_complete_quick()

    messagequeue.resolve({'msg': 'Checking mods finished', 'mods': mod_list})


def _sync_all(messagequeue, launcher_moddir, mods):
    # WARNING: This methods gets called in a different process

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
        if m.up_to_date:
            Logger.info('Not downloading mod {} because it is up to date'.format(m.foldername))
            continue

        m.clientlocation = launcher_moddir  # This change does NOT persist in the main launcher (would be nice :()

        syncer = TorrentSyncer(messagequeue, m)
        sync_ok = syncer.sync(force_sync=False)  # Use force_sync to force full recheck of all the files' checksums

        if sync_ok == False:  # Alpha undocumented feature: stop processing on a reject()
            return

        messagequeue.progress({'msg': '[%s] Mod synchronized.' % (m.foldername,),
                               'workaround_finished': m.foldername}, 1.0)

    messagequeue.resolve({'msg': 'Downloading mods finished.'})


def _protected_call(messagequeue, function, *args, **kwargs):
    try:
        return function(messagequeue, *args, **kwargs)
    except Exception as e:
        stacktrace = "".join(_format_exc_info(*sys.exc_info()))
        error = 'An error occurred in a subprocess:\nBuild: {}\n{}'.format(get_git_sha1_auto(), stacktrace).rstrip()
        messagequeue.reject({'msg': error})


class ModManager(object):
    """docstring for ModManager"""
    def __init__(self):
        super(ModManager, self).__init__()
        self.para = None
        self.sync_para = None
        self.mods = None
        self.settings = kivy.app.App.get_running_app().settings

    def prepare_and_check(self):
        self.para = Para(_protected_call, (_prepare_and_check, self.settings.get_launcher_moddir()), 'checkmods')
        self.para.then(self.on_prepare_and_check_resolve, None, None)
        self.para.run()
        return self.para

    def sync_all(self):
        self.sync_para = Para(_protected_call,
            (_sync_all, self.settings.get_launcher_moddir(), self.mods), 'sync')
        self.sync_para.then(None, None, self.on_sync_all_progress)
        self.sync_para.run()
        return self.sync_para

    def on_prepare_and_check_resolve(self, data):
        Logger.info('ModManager: Got mods ' + repr(data['mods']))
        self.mods = data['mods']

    def on_sync_all_progress(self, data, progress):
        Logger.debug('ModManager: Sync progress ' + repr(data))
        # Todo: modlist could be a class of its own

        mod_synchronised = data.get('workaround_finished')
        if mod_synchronised:
            for mod in self.mods:
                if mod.foldername == mod_synchronised:
                    mod.up_to_date = True


if __name__ == '__main__':
    pass
