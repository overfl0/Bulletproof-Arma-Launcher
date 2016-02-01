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
import sys

from datetime import datetime

import kivy
import kivy.app  # To keep PyDev from complaining
from kivy.logger import Logger
import requests
import textwrap

from third_party import teamspeak
from third_party.arma import Arma, SoftwareNotInstalled
from utils.devmode import devmode
from utils.app import BaseApp
from utils.primitive_git import get_git_sha1_auto
from utils.process import Para
from utils.testtools_compat import _format_exc_info
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


def _get_mod_descriptions(para):
    # WARNING: This methods gets called in a different process
    """
    helper function to get the moddescriptions from the server

    this function is ment be used threaded or multiprocesses, you have
    to pass in a queue
    """
    para.progress({'msg': 'Downloading mod descriptions'})

    domain = devmode.get_launcher_domain(default='launcher.tacbf.com')
    metadata_path = devmode.get_metadata_path(default='/tacbf/updater/metadata.json')
    url = 'http://{}{}'.format(domain, metadata_path)

    res = requests_get_or_reject(para, domain, url, verify=False, timeout=10)

    if res.status_code != 200:
        para.reject({'details': '{}\n{}\n\n{}'.format(
            'Mods descriptions could not be received from the server',
            'Status Code: ' + unicode(res.status_code), res.text)})
    else:
        try:
            data = res.json()
        except ValueError:
            Logger.error('ModManager: Failed to parse mods descriptions json!')
            stacktrace = "".join(_format_exc_info(*sys.exc_info()))
            para.reject({'details': '{}\n\n{}'.format(
                'Mods descriptions could not be parsed', stacktrace)})

        # Temporary! Ensure alpha version is correct
        if data.get('alpha') not in ("4.1", "5", "6"):
            error_message = 'This launcher is out of date! You won\'t be able do download mods until you update to the latest version!'
            Logger.error(error_message)
            para.reject({'msg': error_message})
            return ''

    para.resolve({'msg': 'Downloading mods descriptions finished',
                  'data': data})

    return data


def convert_metadata_to_mod(md, downloadurlPrefix):
    # TODO: This should be a constructor of the Mod class
    # parse timestamp
    tsstr = md.get('torrent-timestamp')
    md['torrent-timestamp'] = parse_timestamp(tsstr)
    md['downloadurl'] = "{}{}-{}.torrent".format(downloadurlPrefix,
                                                 md['foldername'],
                                                 tsstr)

    mod = Mod.fromDict(md)

    return mod


def get_launcher_description(para, launcher_moddir, metadata):
    downloadurlPrefix = 'http://91.121.120.221/tacbf/updater/torrents/'

    if 'launcher' not in metadata:
        return None

    launcher = metadata['launcher']
    launcher_mod = convert_metadata_to_mod(launcher, downloadurlPrefix)
    launcher_mod.clientlocation = launcher_moddir  # TODO: Change this

    return launcher_mod


def process_description_data(para, data, launcher_moddir):
    domain = devmode.get_launcher_domain(default='launcher.tacbf.com')
    downloadurlPrefix = 'http://{}/tacbf/updater/torrents/'.format(domain)
    mods = []

    for md in data['mods']:
        mod = convert_metadata_to_mod(md, downloadurlPrefix)
        mod.clientlocation = launcher_moddir
        mods.append(mod)

        Logger.debug('ModManager: Got mods descriptions: ' + repr(md))

    return mods


def _prepare_and_check(messagequeue, launcher_moddir, mod_descriptions_data):
    # WARNING: This methods gets called in a different process
    launcher = get_launcher_description(messagequeue, launcher_moddir, mod_descriptions_data)
    mod_list = process_description_data(messagequeue, mod_descriptions_data, launcher_moddir)

    # Debug mode: decrease the number of mods to download
    mods_filter = devmode.get_mods_filter()
    if mods_filter:
        # Keep only the mods with names starting with any of the giver filters
        mod_list = [mod for mod in mod_list if any(mod.name.startswith(prefix) for prefix in mods_filter)]

    # TODO: Perform a better check here. Should compare md5sum with actual launcher, etc...
    # TODO: Change this to a static function
    launcher_syncer = TorrentSyncer(messagequeue, launcher)
    launcher.up_to_date = launcher_syncer.is_complete_quick()

    # check if any oth the mods is installed with withSix
    messagequeue.progress({'msg': 'Checking mods'})
    for m in mod_list:
        # TODO: Change this to a static function
        syncer = TorrentSyncer(messagequeue, m)
        m.up_to_date = syncer.is_complete_quick()

    messagequeue.resolve({'msg': 'Checking mods finished', 'mods': mod_list, 'launcher': launcher})


def _tfr_post_download_hook(message_queue, mod):
    """Copy TFR configuration files and install the TeamSpeak plugin.
    In case of errors, show the appropriate message box.
    """
    # WARNING: This methods gets called in a different process

    def _show_message_box(message_queue, title, message, markup=True):
        message_queue.progress({'msg': 'Installing TFR TeamSpeak plugin...',
                                'message_box': {
                                    'text': message,
                                    'title': title,
                                    'markup': markup
                                }
                                }, 1.0)

    tfr_directory = '@task_force_radio'
    if mod.foldername != tfr_directory:
        return

    path_tfr = os.path.join(mod.clientlocation, tfr_directory)
    path_userconfig = os.path.join(path_tfr, 'userconfig')
    path_ts3_addon = os.path.join(path_tfr, 'TeamSpeak 3 Client')
    path_ts_plugins = os.path.join(path_ts3_addon, 'plugins')
    path_installed_plugins = os.path.join(teamspeak.get_install_location(), 'plugins')

    installation_failed_message = textwrap.dedent("""
        Task Force Arrowhead Radio has been downloaded or updated.

        Automatic installation of TFR failed.


        To finish the installation of TFR, you need to:

        1) Manually copy the files from [ref={}][color=3572b0]TeamSpeak 3 Client\\plugins[/color][/ref] directory
            to [ref={}][color=3572b0]your Teamspeak directory[/color][/ref].
        2) Enable the TFR plugin in Settings->Plugins in Teamspeak.""".format(
        path_ts_plugins, path_installed_plugins))

    run_admin_message = textwrap.dedent("""
        Task Force Arrowhead Radio has been downloaded or updated.

        In order to install the Task Force Radio TeamSpeak plugin you need to run the
        plugin installer as Administrator.


        If you do not want to do that, you need to:

        1) Manually copy the files from [ref={}][color=3572b0]TeamSpeak 3 Client\\plugins[/color][/ref] directory
            to [ref={}][color=3572b0]your Teamspeak directory[/color][/ref].
        2) Enable the TFR plugin in Settings->Plugins in Teamspeak.""".format(
        path_ts_plugins, path_installed_plugins))

    installation_succeeded_message = textwrap.dedent("""
        Task Force Arrowhead Radio has been downloaded or updated.

        To finish the installation of TFR, you need to enable the TFR plugin in
        Settings->Plugins in Teamspeak.""")

    message_queue.progress({'msg': 'Copying TFR configuration...'}, 1.0)
    teamspeak.copy_userconfig(path=path_userconfig)

    message_queue.progress({'msg': 'Installing TFR TeamSpeak plugin...'}, 1.0)
    install_instance = teamspeak.install_unpackaged_plugin(path=path_ts3_addon)
    if not install_instance:
        _show_message_box(message_queue, title='Run TFR TeamSpeak plugin installer!', message=run_admin_message)
        install_instance = teamspeak.install_unpackaged_plugin(path=path_ts3_addon)

    if install_instance:
        exit_code = install_instance.wait()
        if exit_code != 0:
            _show_message_box(message_queue, title='TFR TeamSpeak plugin installation failed!', message=installation_failed_message)
            message_queue.reject({'details': 'TeamSpeak plugin installation terminated with code: {}'.format(exit_code)})
            return False
        else:
            _show_message_box(message_queue, title='Action required!', message=installation_succeeded_message)

    else:
        message_queue.reject({'msg': 'The user cancelled the TeamSpeak plugin installation.'})
        return False

    return True


def _sync_all(message_queue, launcher_moddir, mods):
    """Run syncers for all the mods sequentially and then their post-download hooks."""
    # WARNING: This methods gets called in a different process
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

        syncer = TorrentSyncer(message_queue, m)
        sync_ok = syncer.sync(force_sync=False)  # Use force_sync to force full recheck of all the files' checksums

        if sync_ok is False:  # Alpha undocumented feature: stop processing on a reject()
            return

        # Will only fire up if mod == TFR
        if _tfr_post_download_hook(message_queue, m) == False:
            return  # Alpha undocumented feature: stop processing on a reject()

        message_queue.progress({'msg': '[%s] Mod synchronized.' % (m.foldername,),
                                'workaround_finished': m.foldername}, 1.0)

    message_queue.resolve({'msg': 'Downloading mods finished.'})


def _protected_call(messagequeue, function, *args, **kwargs):
    try:
        return function(messagequeue, *args, **kwargs)
    except Exception:
        stacktrace = "".join(_format_exc_info(*sys.exc_info()))
        error = 'An error occurred in a subprocess:\nBuild: {}\n{}'.format(get_git_sha1_auto(), stacktrace).rstrip()
        messagequeue.reject({'details': error})


class ModManager(object):
    """docstring for ModManager"""
    def __init__(self):
        super(ModManager, self).__init__()
        self.para = None
        self.sync_para = None
        self.launcher_sync_para = None
        self.mods = None
        self.launcher = None
        self.settings = kivy.app.App.get_running_app().settings

    def download_mod_description(self):
        self.para = Para(_protected_call, (_get_mod_descriptions,), 'download_description')
        self.para.run()
        return self.para

    def prepare_and_check(self, data):
        self.para = Para(_protected_call, (_prepare_and_check, self.settings.get_launcher_moddir(), data), 'checkmods')
        self.para.then(self.on_prepare_and_check_resolve, None, None)
        self.para.run()
        return self.para

    def sync_all(self):
        self.sync_para = Para(_protected_call, (_sync_all, self.settings.get_launcher_moddir(), self.mods), 'sync')
        self.sync_para.then(None, None, self.on_sync_all_progress)
        self.sync_para.run()
        return self.sync_para

    def sync_launcher(self):
        self.launcher_sync_para = Para(_protected_call,
            (_sync_all, self.settings.get_launcher_moddir(), [self.launcher]), 'sync')
        self.launcher_sync_para.then(None, None, self.on_sync_all_progress)
        self.launcher_sync_para.run()
        return self.launcher_sync_para

    def on_prepare_and_check_resolve(self, data):
        Logger.info('ModManager: Got mods ' + repr(data['mods']))
        self.mods = data['mods']
        self.launcher = data['launcher']

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
