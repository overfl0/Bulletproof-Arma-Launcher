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

import ConfigParser
import os
import textwrap
import urllib
import zipfile

from kivy.logger import Logger
from third_party import SoftwareNotInstalled
from third_party.clientquery import get_TS_servers_connected
from utils import process_launcher
from utils import system_processes
from utils import walker
from utils.admin import run_admin
from utils.devmode import devmode
from utils.hashes import sha1
from utils.registry import Registry


class TeamspeakNotInstalled(SoftwareNotInstalled):
    pass


def get_executable_path():
    """Return the path of the teamspeak executable.
    Guesses the path by looking at the executable in the install location.
    """

    if devmode.get_ts_executable():
        return devmode.get_ts_executable()

    install_location = get_install_location()
    matches = ['ts3client_win32.exe', 'ts3client_win64.exe']

    for match in matches:
        exe_file = os.path.join(install_location, match)
        if os.path.isfile(exe_file):
            return exe_file

    error_message = textwrap.dedent("""\
        Could not find the TS executable path.

        The following directory was retrieved from your Windows registry
        and searched for the executables:
        {}

        None of the following executables were found there:
        {}\
    """).format(install_location, '\n'.join('- ' + match for match in matches))

    raise TeamspeakNotInstalled(error_message)


def get_addon_installer_path():
    """Return the path of the addon installer for teamspeak.
    Guesses the path by looking at the executable in the install location.
    """

    if devmode.get_ts_addon_installer():
        return devmode.get_ts_addon_installer()

    install_location = get_install_location()
    match = 'package_inst.exe'

    exe_file = os.path.join(install_location, match)
    if os.path.isfile(exe_file):
        Logger.info('TS: Guessed TS installer path: {}'.format(exe_file))
        return exe_file

    error_message = textwrap.dedent("""\
        Could not get the TS plugin installer path.

        The following directory was retrieved from your Windows registry
        and searched for the executable:
        {}

        The following executable was not found there:
        {}\
    """).format(install_location, match)

    raise TeamspeakNotInstalled(error_message)


def get_install_location():
    """Return the path to where teamspeak executables are installed."""

    if devmode.get_ts_install_location():
        return devmode.get_ts_install_location()

    try:
        key = 'SOFTWARE\\TeamSpeak 3 Client'
        reg_val = Registry.ReadValueMachineAndUser(key, '', True)
        return reg_val

    except Registry.Error:
        raise TeamspeakNotInstalled('Could not get the TS install location')


def _get_config_location():
    """Return the value meaning where the user configuration is stored.
      0 - C:/Users/<username>/AppData/Roaming/TS3Client
      1 - Installation folder (get_install_location()/config).
    The actual directory may not exist until the user actually launches Teamspeak!
    """

    if devmode.get_ts_config_location():
        return devmode.get_ts_config_location()

    try:
        key = 'SOFTWARE\\TeamSpeak 3 Client'
        reg_val = Registry.ReadValueMachineAndUser(key, 'ConfigLocation', True)
        return reg_val

    except Registry.Error:
        raise TeamspeakNotInstalled('Could not get the TS config location information')


def get_config_location():
    """Return the directory where the configuration should be stored.
    The actual directory may not exist until the user actually launches Teamspeak!
    """

    regedit_value = _get_config_location()

    if regedit_value == '1':
        return os.path.join(get_install_location(), 'config')
    elif regedit_value == '0':
        return os.path.expandvars('%APPDATA%\\TS3Client')
    else:
        raise TeamspeakNotInstalled('Bad registry value: {}'.format(regedit_value))


def get_plugins_locations():
    """Return the paths where plugins may be located.
    Because there is no way of easily telling TS 3.0 and 3.1 apart, and that
    they have changed the way of storing plugins, we have to return both
    probable locations to check.
    """

    return [get_install_location(), get_config_location()]


def check_installed():
    """Run all the registry checks. If any of them fails, raises TeamspeakNotInstalled()."""

    executable_path = get_executable_path()
    addon_installer_path = get_addon_installer_path()
    install_location = get_install_location()
    config_location = get_config_location()

    Logger.info('TS: executable path: {}'.format(executable_path))
    Logger.info('TS: addon installer path: {}'.format(addon_installer_path))
    Logger.info('TS: install location: {}'.format(install_location))
    Logger.info('TS: config location: {}'.format(config_location))

    if not os.path.isfile(addon_installer_path):
        raise TeamspeakNotInstalled('Could not find TeamSpeak addon installer which should be located at:\n{}'.
                                    format(addon_installer_path))

    if not os.path.isfile(executable_path):
        raise TeamspeakNotInstalled('Could not find TeamSpeak executable which should be located at:\n{}'.
                                    format(executable_path))


def is_teamspeak_running():
    """Check if a TeamSpeak process is running."""

    ts3_path = get_executable_path()
    # May result in a false negative if you don't have the permission to access
    # the process
    if system_processes.file_running(ts3_path):
        return True

    if system_processes.program_running('ts3client_win32.exe', 'ts3client_win64.exe'):
        return True

    return False


def _sanitize_url(url):
    """Replace all the characters with their %xx equivalents for all but the
    basic characters.
    """
    if not url:
        return url

    return urllib.quote(urllib.unquote(url), ':')


def run_and_connect(urls):
    """Run the teamspeak client and connect to the first TS server if the user
    is not already connected to any of the servers in the list.

    This allows passing several addresses that the users may be using, like
    both the human-readable url and IP:port pair.
    """

    url_to_open = urls[0]

    if is_teamspeak_running():
        api_key = get_api_key()
        ts_servers = get_TS_servers_connected(api_key)
        for url in urls:
            host = url.split(':')[0]

            if host in ts_servers:
                Logger.info('TS: Teamspeak process found running and already connected to the right TS server.')
                return

        Logger.info('TS: Teamspeak process found running but NOT connected to any of the right TS server(s).')
    else:
        Logger.info('TS: Running Teamspeak process not found.')

    full_url = 'ts3server://{}'.format(_sanitize_url(url_to_open))
    Logger.info('TS: Connecting to teamspeak server: {} using the executable: {}'.format(full_url, get_executable_path()))
    call_args = [get_executable_path(), full_url]
    process_launcher.run(call_args, shell=True)


def create_package_ini_file_contents(path, name, author, version, platforms, description):
    """Create a package.ini file at <path> for a future ts3_plugin file."""
    package_ini = textwrap.dedent("""Name = {}
                                     Type = Plugin
                                     Author = {}
                                     Version = {}
                                     Platforms = {}
                                     Description = "{}"
    """).format(name, author, version, ', '.join(platforms), description)

    return package_ini


def create_ts3_plugin_package(path, name, author, version, platforms, description):
    """Create a teamspeak ts3_plugin file from files in <path>/plugins.
    The created file will be called tfr.ts3_plugin, will be a zip file and will
    contain the <path>/plugins directory and an autogenerated package.ini file.
    """

    ts3_plugin_path = os.path.join(path, 'tfr.ts3_plugin')

    package_ini_contents = create_package_ini_file_contents(
        path=path, name=name, author=author, version=version,
        platforms=platforms, description=description)

    zipf = zipfile.ZipFile(ts3_plugin_path, 'w')
    zipf.writestr('package.ini', package_ini_contents.encode('utf-8'))

    for root, _, files in walker.walk(os.path.join(path, 'plugins')):
        for file_entry in files:
            file_path = os.path.join(root, file_entry)

            base_offset = len(path)
            if not path.endswith(os.path.sep):
                base_offset += 1

            # Strip the base path from the file path in the archive
            archive_path = file_path[base_offset:]

            # Note There is no official file name encoding for ZIP files.
            # If you have unicode file names, you must convert them to byte
            # strings in your desired encoding before passing them to write().
            # WinZip interprets all file names as encoded in CP437, also known
            # as DOS Latin.
            zipf.write(file_path, archive_path.encode('cp437'))

    zipf.close()

    return ts3_plugin_path


def install_ts3_plugin(path):
    """Install a ts3_plugin file by calling the Teamspeak plugin installer.
    Return exit_code or None if UAC promt was rejected by the user.
    """

    args = [get_addon_installer_path(), '-silent', path]

    '''
    # This was dropped because it was too unreliable
    if not only_as_root:
        handle = process_launcher.run(args)
        retval = handle.wait()

        if retval == 0:  # TODO: AND CHECK FOR FILES FAILS!
            return retval
    '''

    handle = run_admin(args[0], args[1:])
    if handle is None:
        return handle

    return handle.wait()


def install_unpackaged_plugin(path):
    """Package a plugin located at <path> to a ts3_plugin file and then install it.
    The created ts3_plugin file will be left in place because we cannot know when
    the installer terminates, yet.
    """

    version = 'Unknown'

    tfr_package = create_ts3_plugin_package(
        path,
        name='Task Force Arma 3 Radio',
        author='[TF]Nkey',
        version=version,
        platforms=['win32', 'win64'],
        description='Task Force Arrowhead Radio.\nPlugin packaged automatically by Torrent Launcher team.'
    )

    return install_ts3_plugin(tfr_package)


def compute_checksums_for_ts3_plugin(zip_filename):
    """Create a dictionary of file paths (with separators matching the OS
    separator) along with SHA1 checksums of those files.
    """
    checksums = {}

    with zipfile.ZipFile(zip_filename) as zip_handle:
        for file_info in zip_handle.infolist():
            # Ignore package.ini
            if file_info.filename == 'package.ini':
                continue

            # Ignore directories
            if file_info.filename.endswith('/'):
                continue

            handle = zip_handle.open(file_info)
            try:
                checksum = sha1(handle)
            finally:
                handle.close()

            # The separator for zip files is always '/' internally
            filename_os = file_info.filename.replace('/', os.path.sep)
            checksums[filename_os] = checksum

    return checksums


def ts3_plugin_is_valid(zip_filename):
    """Return True if the given ts3_plugin is valid or return an error message."""

    with zipfile.ZipFile(zip_filename) as zip_handle:

        filenames = zip_handle.namelist()
        if 'package.ini' not in filenames:
            error = 'File "package.ini" is missing'
            Logger.error('ts3_plugin_is_valid: {} from {}'.format(error, zip_filename))
            return error

        if 'plugins/' not in filenames:
            error = 'Directory "plugins" is missing'
            Logger.error('ts3_plugin_is_valid: {} from {}'.format(error, zip_filename))
            return error

    return True


def get_api_key():
    """Return the clientquery api key from Teamspeak config directory."""

    clientquery_ini = os.path.join(get_config_location(), 'clientquery.ini')
    if not os.path.isfile(clientquery_ini):
        Logger.info('ClientQuery: Could not find clientquery.ini. Assuming no api key')
        return None

    try:
        config = ConfigParser.RawConfigParser(allow_no_value=True)
        config.read(clientquery_ini)
        api_key = config.get('General', 'api_key')

        return api_key

    except Exception as ex:
        Logger.error('ClientQuery: get_api_key: {}'.format(ex))
        return None


if __name__ == '__main__':
    print get_api_key()
