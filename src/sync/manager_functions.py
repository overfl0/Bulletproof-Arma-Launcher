# Bulletproof Arma Launcher
# Copyright (C) 2016 Sascha Ebert
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

import launcher_config
import os
import textwrap
import time

from datetime import datetime
from distutils.version import LooseVersion
from kivy.logger import Logger
from kivy.config import Config
from sync import integrity, torrent_utils
from sync.mod import Mod
from sync.server import Server
from sync.torrentsyncer import TorrentSyncer
from third_party import teamspeak
from utils.devmode import devmode
from utils.requests_wrapper import download_url, DownloadException

default_log_level = devmode.get_log_level('info')
Config.set('kivy', 'log_level', default_log_level)

################################################################################
################################## ATTENTION!!! ################################
################################################################################
#
#
# Everything below this comment is run IN A DIFFERENT PROCESS!
# To communicate with the main program, you have to use the resolve(), reject()
# and progress() calls of the message queue!
#
#
################################################################################
################################## ATTENTION!!! ################################
################################################################################


def parse_timestamp(ts):
    """
    Parse a timestamp that looks like this:
    YYYY-MM-DD_Epoch

    we parse Epoch in utc time. After that make sure to use it like utc
    """
    s = ts.split('_')
    stamp = s[1]
    return datetime.utcfromtimestamp(float(stamp))


def create_timestamp(epoch):
    """
    Create a timestamp that looks like this:
    YYYY-MM-DD_Epoch
    """
    return datetime.fromtimestamp(int(epoch)).strftime('%Y-%m-%d_') + str(int(epoch))


def symlink_mod(message_queue, mod_location, real_location):
    """Just create a symlink for a mod and resolve."""

    try:
        torrent_utils.symlink_mod(mod_location, real_location)
        message_queue.resolve(real_location)

    except torrent_utils.AdminRequiredError as ex:
        message_queue.reject({'msg': ex.message})


def _get_mod_descriptions(para, login, password):
    """
    helper function to get the moddescriptions from the server

    this function is ment be used threaded or multiprocesses, you have
    to pass in a queue
    """
    para.progress({'msg': 'Downloading mod descriptions'})

    domain = devmode.get_launcher_domain(default=launcher_config.domain)
    metadata_path = devmode.get_metadata_path(default=launcher_config.metadata_path)
    url = 'http://{}{}'.format(domain, metadata_path)

    try:
        if login and password:
            res = download_url(domain, url, timeout=5, auth=(login, password))
        else:
            res = download_url(domain, url, timeout=5)
    except DownloadException as ex:
        para.reject({'msg': 'Downloading metadata: {}'.format(ex.args[0])})


    if res.status_code == 404:
        message = textwrap.dedent('''\
            Metadata could not be downloaded from the master server.
            Reason: file not found on the server (HTTP 404).

            This may be because the mods are updated on the server right now.
            Please try again in a few minutes.
            ''')
        para.reject({'msg': message})

    elif res.status_code != 200:
        message = textwrap.dedent('''\
            Metadata could not be downloaded from the master server.
            HTTP error code: {}

            Contact the master server owner to fix this issue.
            '''.format(unicode(res.status_code)))
        para.reject({'msg': message})

    else:
        try:
            data = res.json()
        except ValueError:
            Logger.error('ModManager: Failed to parse mods descriptions json!')
            message = textwrap.dedent('''
                Failed to parse metadata received from the master server.

                Contact the master server owner to fix this issue.

                If you're the master server owner, consider checking your
                metadata.json file with a JSON validator.
                '''.format(unicode(res.status_code)))
            para.reject({'msg': message})

        # Protection in case autoupdate is messed up and we have to force a manual update
        protocol = '1.0'
        required_protocol = data.get('protocol')
        if not required_protocol or LooseVersion(protocol) < LooseVersion(required_protocol):
            error_message = 'This launcher is out of date! You won\'t be able to download mods until you update to the latest version!'
            Logger.error(error_message)
            para.reject({'msg': error_message})
            return ''

    para.resolve({'msg': 'Downloading mods descriptions finished',
                  'data': data})

    return data


def convert_metadata_to_mod(md, torrent_url_prefix):
    # TODO: This should be a constructor of the Mod class
    # parse timestamp
    tsstr = md.get('torrent-timestamp')
    md['torrent-timestamp'] = parse_timestamp(tsstr)
    md['torrent_url'] = "{}{}-{}.torrent".format(torrent_url_prefix,
                                                 md['foldername'],
                                                 tsstr)

    mod = Mod.fromDict(md)

    return mod


def _torrent_url_base():
    domain = devmode.get_launcher_domain(default=launcher_config.domain)
    torrents_path = devmode.get_torrents_path(default=launcher_config.torrents_path)
    torrent_url_prefix = 'http://{}{}/'.format(domain, torrents_path)

    return torrent_url_prefix

def parse_launcher_data(para, metadata, launcher_basedir):
    if 'launcher' not in metadata:
        return None

    launcher = metadata['launcher']
    launcher_mod = convert_metadata_to_mod(launcher, _torrent_url_base())
    launcher_mod.parent_location = launcher_basedir
    launcher_mod.is_launcher = True

    return launcher_mod


def parse_mods_data(para, data, launcher_moddir):
    mods = []

    for md in data.get('mods', []):
        mod = convert_metadata_to_mod(md, _torrent_url_base())
        mod.parent_location = launcher_moddir
        mods.append(mod)

        Logger.debug('ModManager: Got mods descriptions: ' + repr(md))

    return mods


def parse_teamspeak_data(para, data):
    teamspeak = data.get('teamspeak')

    return teamspeak

def parse_battleye_data(para, data):
    battleye = data.get('battleye')

    return battleye

def parse_servers_data(para, data, launcher_moddir):
    servers = []

    servers_list = data.get('servers')
    if not servers_list:
        para.reject({'msg': 'No servers present in the metadata!\nContact the master server owner!'})
        raise Exception('No servers present in the metadata!\nContact the master server owner!')

    for server_entry in servers_list:
        for arg in ['name', 'ip', 'port']:
            if arg not in server_entry:
                para.reject({'msg': 'The server is missing the {} field in the metadata!\nContact the master server owner!'.format(arg)})
                raise Exception('The server is missing the {} field in the metadata!\nContact the master server owner!'.format(arg))

        server = Server.fromDict(server_entry)

        # Add the server mods is available
        if 'mods' in server_entry:
            server.add_mods(parse_mods_data(para, server_entry, launcher_moddir))

        server.teamspeak = parse_teamspeak_data(para, server_entry)
        server.battleye = parse_battleye_data(para, server_entry)

        servers.append(server)

    return servers


def _prepare_and_check(messagequeue, launcher_moddir, launcher_basedir,
                       mod_descriptions_data, selected_optional_mods):
    launcher = parse_launcher_data(messagequeue, mod_descriptions_data, launcher_basedir)
    mods_list = parse_mods_data(messagequeue, mod_descriptions_data, launcher_moddir)
    servers_list = parse_servers_data(messagequeue, mod_descriptions_data, launcher_moddir)
    teamspeak = parse_teamspeak_data(messagequeue, mod_descriptions_data)
    battleye = parse_battleye_data(messagequeue, mod_descriptions_data)

    # Set the selection flag near for all the mods that have been selected
    # by the user
    for mod in mods_list:
        if mod.foldername in selected_optional_mods:
            mod.selected = True

        for server in servers_list:
            for mod in server.mods:
                if mod.foldername in selected_optional_mods:
                    mod.selected = True

    # Debug mode: decrease the number of mods to download
    mods_filter = devmode.get_mods_filter()
    if mods_filter:
        # Keep only the mods with names starting with any of the giver filters
        mods_list = [mod for mod in mods_list if any(mod.full_name.startswith(prefix) for prefix in mods_filter)]

        for server in servers_list:
            server.set_mods([mod for mod in server.mods if any(mod.full_name.startswith(prefix) for prefix in mods_filter)])

    messagequeue.progress({'msg': 'Checking mods'})

    if launcher:
        # TODO: Perform a better check here. Should compare md5sum with actual launcher, etc...
        launcher.is_complete()

    for server in servers_list:
        for mod in server.mods:
            mod.is_complete()

    for mod in mods_list:
        mod.is_complete()

    messagequeue.resolve({'msg': 'Checking mods finished',
                          'mods': mods_list,
                          'launcher': launcher,
                          'servers': servers_list,
                          'teamspeak': teamspeak,
                          'battleye': battleye,
                          })


def _tsplugin_wait_for_requirements(message_queue):
    """Wait until the user clicks OK and they close any running TeamSpeak instance.
    Ugly workaround but it works ;)
    During this time, any other messages save for 'terminate' are DISCARDED!
    As a workaround, return the message received (has to be then checked if
    equal to 'terminate')

    This is required because if we don't wait until the user does *something*
    and just show the UAC prompt, the prompt is going to timeout automatically
    after 2 minutes of inactivity.
    By requiring the user to click OK, we are ensuring that he actually is in
    front of the computer and can act upon the UAC prompt before it timeouts.
    """

    run_tsplugin_install_message = textwrap.dedent("""
        A mod containing a Teamspeak plugin has been downloaded or updated.

        The launcher will next prompt you and ask you for permission to install the
        plugin as Administrator.

        Close TeamSpeak if it is running to continue with the installation.
        """)

    message_queue.progress({'msg': 'Installing TeamSpeak plugin...',
                            'tsplugin_request_action': True,
                            'message_box': {
                                'text': run_tsplugin_install_message,
                                'title': 'Run TeamSpeak plugin installer!',
                                'markup': False
                            }
                            }, 1.0)

    Logger.info('TS installer: Waiting for the user to acknowledge TS plugin installation.')
    user_acknowledged = False
    while True:

        message = message_queue.receive_message()
        if not message:

            if user_acknowledged:
                if teamspeak.is_teamspeak_running():
                    message = 'Waiting for TeamSpeak to be closed. Close TeamSpeak to continue the installation!'
                    Logger.info('TS installer: {}'.format(message))
                    message_queue.progress({'msg': message}, 1.0)
                else:
                    break  # We can continue the installation

            time.sleep(0.5)
            continue

        command = message.get('command')

        if command == 'tsplugin_install_as_admin':
            Logger.info('TS installer: Received continue command. Installing TS plugin...')
            user_acknowledged = True

        if command == 'terminate':
            Logger.info('TS installer: Caller wants termination')
            return command

    return 'tsplugin_install_as_admin'


def _try_installing_teamspeak_plugins(message_queue, mod):
    """Install any Teamspeak plugins found in the mod files.
    In case of errors, show the appropriate message box.
    """

    def _show_message_box(message_queue, title, message, markup=True):
        message_queue.progress({'msg': 'Installing TeamSpeak plugin...',
                                'message_box': {
                                    'text': message,
                                    'title': title,
                                    'markup': markup
                                }
                                }, 1.0)

    ts3_plugin_files_to_process = []
    ts3_plugins_files = [file_path for file_path in mod.files_list if file_path.endswith('.ts3_plugin')]

    # Ignore Those files if everything is already installed
    for ts3_plugin_file in ts3_plugins_files:
        ts3_plugin_full_path = os.path.join(mod.parent_location, ts3_plugin_file)

        valid_or_message = teamspeak.ts3_plugin_is_valid(ts3_plugin_full_path)
        if valid_or_message is not True:
            error_message = textwrap.dedent('''
                A Teamspeak plugin file is not valid!

                Mod: {}
                File name: {}
                Reason: {}

                Contact the server administrators!
                ''').format(mod.foldername, ts3_plugin_file, valid_or_message)

            message_queue.reject({'msg': error_message})
            return False

        if not integrity.is_ts3_plugin_installed(ts3_plugin_full_path):
            ts3_plugin_files_to_process.append(ts3_plugin_file)

    if not ts3_plugin_files_to_process:
        return

    # Inform the user he is about to be asked to install TS plugins
    command = _tsplugin_wait_for_requirements(message_queue)
    if command == 'terminate':  # Workaround for termination request while waiting
        message_queue.reject({'details': 'Para was asked to terminate by the caller'})
        return False

    message_queue.progress({'msg': 'Waiting for permission to install the plugin as Administrator...'}, 1.0)

    for ts3_plugin_file in ts3_plugin_files_to_process:

        ts3_plugin_full_path = os.path.join(mod.parent_location, ts3_plugin_file)

        installation_failed_message = textwrap.dedent("""
            A mod containing a Teamspeak plugin has been downloaded or updated.

            [color=ff0000]Automatic installation of a Teamspeak plugin failed.[/color]
            Remember that you have to run Teamspeak at least once before installing
            any plugins!

            To finish the installation of the Teamspeak plugin, you need to:
            Manually install the plugin: [ref={}][color=3572b0]>> Click here! <<[/color][/ref]
            """.format(os.path.dirname(ts3_plugin_full_path)))

        run_admin_message = textwrap.dedent("""
            A mod containing a Teamspeak plugin has been downloaded or updated.

            In order to install the TeamSpeak plugin you need to run the
            plugin installer as Administrator.

            If you do not want to do that, you need to:
            Manually install the plugin: [ref={}][color=3572b0]>> Click here! <<[/color][/ref]
            """.format(os.path.dirname(ts3_plugin_full_path)))

        exit_code = teamspeak.install_ts3_plugin(path=ts3_plugin_full_path)

        if exit_code is None:
            _show_message_box(message_queue, title='Run TeamSpeak plugin installer!', message=run_admin_message)
            # install_instance = teamspeak.install_unpackaged_plugin(path=path_ts3_addon)
            exit_code = teamspeak.install_ts3_plugin(path=ts3_plugin_full_path)

        if exit_code is None:
            message_queue.reject({'msg': 'The user cancelled the TeamSpeak plugin installation.'})
            return False

        elif exit_code != 0:
            _show_message_box(message_queue, title='TeamSpeak plugin installation failed!', message=installation_failed_message)
            message_queue.reject({'msg': 'TeamSpeak plugin installation terminated with code: {}'.format(exit_code)})
            return False

    return True


def _sync_all(message_queue, mods, max_download_speed, max_upload_speed, seed):
    """Run syncers for all the mods in parallel and then their post-download hooks."""

    syncer = TorrentSyncer(message_queue, mods, max_download_speed, max_upload_speed)
    ip_whitelist = devmode.get_ip_whitelist(default=[])
    if ip_whitelist:
        Logger.info('_sync_all: Setting whitelist: {}'.format(ip_whitelist))
        syncer.set_whitelist_filter(ip_whitelist)

    sync_ok = syncer.sync(force_sync=False, just_seed=seed)  # Use force_sync to force full recheck of all the files' checksums

    # If we had an error or we're closing the launcher, don't call post_download_hooks
    if sync_ok is False or syncer.force_termination:
        # If termination has been forced, issue a resolve so no error is raised.
        # If not sync_ok, a reject has already been issued
        if syncer.force_termination:
            message_queue.resolve({'msg': 'Syncing finished.'})
            return

    # Perform post-download hooks for updated mods
    for m in mods:
        # If the mod had to be updated and the download was performed successfully
        if not m.is_complete() and m.finished_hook_ran:
            # Will only fire up if mod == TFR
            if _try_installing_teamspeak_plugins(message_queue, m) == False:
                return  # Alpha undocumented feature: stop processing on a reject()

            message_queue.progress({'msg': '[%s] Mod synchronized.' % (m.foldername,),
                                    'workaround_finished': m.foldername}, 1.0)

    message_queue.resolve({'msg': 'Downloading mods finished.'})
