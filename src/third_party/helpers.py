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

import headtracking
import errno
import kivy.app
import launcher_config
import os
import teamspeak
import textwrap
import utils.system_processes
import shlex

from kivy.logger import Logger
from third_party import steam
from third_party.arma import Arma, ArmaNotInstalled
from utils import unicode_helpers
from utils import exe_version_checker
from utils.devmode import devmode
from view.messagebox import MessageBox


def cancel_dismiss(instance):
    """Returning true will stop the dispatcher and prevent closing the window."""
    return True


def check_requirements_troubleshooting(dummy_var):
    """Show a modal popup with all the checked registry values for debugging purposes."""

    from utils.context import ignore_exceptions
    """Run all the registry checks. If any of them fails, raises TeamspeakNotInstalled()."""

    executable_path = addon_installer_path = install_location = config_location = \
        steam_path = arma_path = user_path = \
        '[color=FF0000]*** Cannot get data! ***[/color]'

    with ignore_exceptions(Exception):
        executable_path = teamspeak.get_executable_path()

    with ignore_exceptions(Exception):
        addon_installer_path = teamspeak.get_addon_installer_path()

    with ignore_exceptions(Exception):
        install_location = teamspeak.get_install_location()

    with ignore_exceptions(Exception):
        config_location = teamspeak.get_config_location()

    with ignore_exceptions(Exception):
        arma_path = Arma.get_installation_path()

    with ignore_exceptions(Exception):
        steam_path = steam.get_steam_exe_path()

    for _ in xrange(10):
        Logger.info('')

    message = textwrap.dedent('''
        All the fields below should point to a location on your drive.
        If one of those fields says "Cannot get data", it means a program is missing and
        must be installed.
        If ALL fields report "Cannot get data" it means something (an antivirus?) is
        actively blocking access to the registry and you must add an exception in this
        software for the launcher.

        {}

        TS executable path: {}
        TS addon installer path: {}
        TS install location: {}
        TS config flag: {}

        Arma location: {}

        Steam location: {}

        {}
        '''.format('*' * 70,
                   executable_path,
                   addon_installer_path,
                   install_location,
                   config_location,
                   arma_path,
                   steam_path,
                   '*' * 70
                   ))
    Logger.info(message)

    box = MessageBox(message, title='Launcher registry troubleshooting.', markup=True,
                     on_dismiss=cancel_dismiss, hide_button=True)
    box.open()

    return False


def arma_not_found_workaround(on_ok, on_error):
    """After performing a file integrity check on Steam, Arma 3 registry entries
    are removed and the launcher cannot use them to get paths.

    Running the Arma 3 launcher fixes this, although the method they use is very
    crude - they just scan their local directory for executables and recreate
    the registry entries if found. The only problem is that only steam knows the
    launcher's directory.

    So what we do here is we run the launcher and then we wait for it to
    recreate the entries and then try to kill its process after the fact.
    """

    from kivy.clock import Clock
    from kivy.uix.label import Label
    from view.themedpopup import ThemedPopup

    message = textwrap.dedent('''
        Running Arma 3 launcher after Steam integrity check.
        Please wait...


        If this takes more than 20 seconds, open it manually.
        After it opens, close the Arma launcher.

                [ref=steam://run/107410][color=3572b0]>> Click here to run the Arma 3 launcher <<[/color][/ref]
        ''')

    from utils import browser  # TODO: Move this

    def open_hyperlink(obj, ref):
        browser.open_hyperlink(ref)

    label = Label(text=message, markup=True)
    label.bind(on_ref_press=open_hyperlink)
    arma_not_found_fix_popup = ThemedPopup(
        title='Fixing registry entries',
        content=label,
        size_hint=(None, None),
        size=(400, 280),
        auto_dismiss=False)

    def start_workaround(dt):
        arma_not_found_fix_popup.open()
        try:
            Arma.run_arma3_launcher()

        except (steam.SteamNotInstalled, OSError):
            on_error()
            return

        Clock.schedule_interval(arma_not_found_tick, 1)

    def arma_not_found_tick(dt):
        Logger.info('Workaround: tick')

        try:
            Arma.get_installation_path()

        except ArmaNotInstalled:
            return  # Wait again for the launcher to start and fix things

        # It's okay, everything has been fixed
        Logger.info('Workaround: Registry entries fixed. Resuming normal workflow.')
        arma_not_found_fix_popup.dismiss()
        try:
            utils.system_processes.kill_program('arma3launcher.exe')
        except:
            pass  # Don't care. Let the user bother about it

        on_ok()
        return False  # Unschedule this function

    try:
        Arma.get_installation_path()
        on_ok()  # Everything is OK, go on!

    except ArmaNotInstalled:
        Logger.error('Helpers: Could not find Arma 3. Trying a workaround...')
        Clock.schedule_once(start_workaround, 0)


def check_requirements(verbose=True):
    """Check if all the required third party programs are installed in the system.
    Return True if the check passed.
    If verbose == true, show a message box in case of a failed check.
    """

    # TODO: move me to a better place
    try:
        teamspeak.check_installed()
    except teamspeak.TeamspeakNotInstalled as ex:
        if verbose:
            try:
                detailed_message = ex.args[0]
                detailed_message += '\n\n'

            except IndexError:
                detailed_message = ''

            message = textwrap.dedent('''
                Your Teamspeak installation is too old or not installed correctly.

                [color=FF0000]{}[/color][ref=https://www.teamspeak.com/downloads][color=3572b0]>> Click here to get Teamspeak <<[/color][/ref]

                (Re)Install Teamspeak and restart the launcher.
                ''').format(detailed_message)
            box = MessageBox(message, title='Teamspeak required!', markup=True,
                             on_dismiss=cancel_dismiss, hide_button=True)
            box.open()

        return False

    try:
        steam.get_steam_exe_path()
    except steam.SteamNotInstalled:
        if verbose:
            message = textwrap.dedent('''
                Steam does not seem to be installed.
                Having Steam is required in order to play {}.

                [ref=http://store.steampowered.com/about/][color=3572b0]>> Click here to get Steam <<[/color][/ref]

                Install Steam and restart the launcher.
                '''.format(launcher_config.launcher_name))

            box = MessageBox(message, title='Steam required!', markup=True,
                             on_dismiss=cancel_dismiss, hide_button=True)
            box.open()

        return False

    try:
        Arma.get_installation_path()
    except ArmaNotInstalled:
        if verbose:
            message = textwrap.dedent('''
                Cannot find Arma 3 installation directory.
                This happens after clicking "Verify integrity of game cache" on Steam.

                [b]To fix this problem you have to run the original Arma 3 launcher once
                or move this launcher directly to Arma 3 directory.
                Afterwards, restart this launcher.[/b]

                [ref=steam://run/107410][color=3572b0]>> Click here to run the Arma 3 launcher <<[/color][/ref]
                ''')

            box = MessageBox(message, title='Arma 3 required!', markup=True,
                             on_dismiss=cancel_dismiss, hide_button=True)
            box.open()

        return False

    # Arma is not using the dev version
    # Note: we assume no 32/64bit forcing because the executables are at the same version anyway
    arma_path = os.path.join(Arma.get_installation_path(), Arma.get_executable())
    Logger.info('check_requirements: Checking for arma exe file version: {}'.format(arma_path))
    arma_version = exe_version_checker.get_version(arma_path)

    if not arma_version:
        Logger.error('check_requirements: Checking the file failed')
    else:
        Logger.info('Got version: {}'.format(arma_version))

        if arma_version.minor % 2:
            Logger.error('check_requirements: The user is using the development branch of Arma!')

            if verbose:
                message = textwrap.dedent('''
                    You seem to be using the Development Build of Arma!

                    You will not be able to connect to the game server while you are using
                    the Development Build.

                    To change this, open Steam and click:
                    Arma 3 -> Properties -> BETAS

                    Then, select "NONE - Opt out of all beta programs" and wait for the
                    game to finish downloading.

                    Afterwards, restart this launcher.[/b]
                    ''')

                box = MessageBox(message, title='Arma 3 Development Build detected!', markup=True,
                                 on_dismiss=cancel_dismiss, hide_button=True)
                box.open()

            return False


    return True


def create_game_parameters():
    settings = kivy.app.App.get_running_app().settings
    args = []

    if settings.get('arma_win64'):
        args.append('-win64')

    if settings.get('arma_win32'):
        args.append('-win32')

    if settings.get('arma_name') and settings.get('arma_name_enabled'):
        args.append('-name=' + settings.get('arma_name'))

    if settings.get('arma_showScriptErrors'):
        args.append('-showScriptErrors')

    if settings.get('arma_noPause'):
        args.append('-noPause')

    if settings.get('arma_window'):
        args.append('-window')

    if settings.get('arma_checkSignatures'):
        args.append('-checkSignatures')

    if settings.get('arma_filePatching'):
        args.append('-filePatching')

    if settings.get('arma_unit') and settings.get('arma_unit_enabled'):
        args.append('-unit=' + settings.get('arma_unit'))

    if settings.get('arma_exThreads') and settings.get('arma_exThreads_enabled'):
        args.append('-exThreads=' + settings.get('arma_exThreads'))

    if settings.get('arma_hugePages'):
        args.append('-hugepages')

    if settings.get('arma_additionalParameters'):
        args.extend(shlex.split(settings.get('arma_additionalParameters')))

    return args

def get_mission_file_parameter():
    """Return an existing mission path file selected in the settings."""

    settings = kivy.app.App.get_running_app().settings

    if settings.get('arma_mission_file') and settings.get('arma_mission_file_enabled'):
        file_path = settings.get('arma_mission_file')

        if os.path.isfile(file_path):
            return file_path

    return None


def run_the_game(mods, ip=None, port=None, password=None, teamspeak_urls=None, battleye=True):
    """Run the game with the right parameters.
    Handle the exceptions by showing an appropriate message on error.
    """

    # Gathering data
    settings = kivy.app.App.get_running_app().settings
    custom_args = create_game_parameters()
    mission_file = get_mission_file_parameter()
    mod_dir = settings.get('launcher_moddir')  # Why from there? This should be in mod.parent_location but it isn't!

    mods_paths = []
    for mod in mods:
        mod_full_path = os.path.join(mod_dir, mod.foldername)
        mods_paths.append(mod_full_path)

    # Running all the programs
    ts_run_on_start = devmode.get_ts_run_on_start(default=True)
    if ts_run_on_start:
        if teamspeak_urls:
            if isinstance(teamspeak_urls, basestring):
                teamspeak.run_and_connect([teamspeak_urls])
            else:
                teamspeak.run_and_connect(teamspeak_urls)
    else:
        Logger.info('Third party: Not running teamspeak because of devmode settings.')

    if settings.get('run_facetracknoir'):
        Logger.info('Third party: Trying to run FaceTrackNoIR...')
        headtracking.run_faceTrackNoIR()

    if settings.get('run_trackir'):
        Logger.info('Third party: Trying to run TrackIR...')
        headtracking.run_TrackIR()

    if settings.get('run_opentrack'):
        Logger.info('Third party: Trying to run Opentrack...')
        headtracking.run_opentrack()

    Logger.info('Third party: Running the game')
    try:
        _ = Arma.run_game(mod_list=mods_paths,
                          custom_args=custom_args,
                          ip=ip,
                          port=port,
                          password=password,
                          mission_file=mission_file,
                          battleye=battleye,
                          force_32bit='-win32' in custom_args,
                          force_64bit='-win64' in custom_args)
        # Note: although run_game returns an object, due to the way steam works,
        # it is unreliable. You never know whether it is the handle to Arma,
        # Steam or Arma's own launcher.
        # The only way to be sure is to analyze the process list :(

    except ArmaNotInstalled:
        text = "Arma 3 does not seem to be installed."
        no_arma_info = MessageBox(text, title='Arma not installed!')
        no_arma_info.chain_open()

    except steam.SteamNotInstalled:
        text = "Steam does not seem to be installed."
        no_steam_info = MessageBox(text, title='Steam not installed!')
        no_steam_info.chain_open()

    except OSError as ex:
        error_message = unicode_helpers.fs_to_u(ex.strerror)
        text = "Error while launching Arma 3:\n{}.".format(error_message)

        # Give a more specific error message in case of elevation required
        if ex.errno == errno.EINVAL and hasattr(ex, 'winerror') and ex.winerror == 740:
            # ex.winerror == winerror.ERROR_ELEVATION_REQUIRED
            text += textwrap.dedent('''

            Your Steam installation requires Administrator privileges to be run.
            Either run the launcher as Administrator or change required privileges of Steam.exe.

            (right click->properties->Compatibility->Run this program as an administrator)
            ''')

        error_info = MessageBox(text, title='Error while launching Arma 3!')
        error_info.chain_open()

    arma_may_be_running(newly_launched=True)

ARMA_PROCESS_EVER_SEEN = False
ARMA_PROCESS_TERMINATED = True


def arma_may_be_running(newly_launched=False):
    """Check if arma3.exe *may be* running in the system.

    If newly_launched = True, the function will assume that the process may
    still be being launched and will return True until the exe is found and then
    disappears from the list of the processes.

    This function returns False if Arma 3 has been found to be running in the
    past and is not running anymore. This answer is 100% sure.

    If the function returns True it either means Arma is running now (100% sure)
    or that the process is now being launched but arma3.exe has not yet been
    seen in the system. In case there is a problem while running Arma, this
    function will return True forever.
    It is unknown at this point if there is some other reliable way of telling
    whether Arma is being launched or not.
    """

    global ARMA_PROCESS_EVER_SEEN
    global ARMA_PROCESS_TERMINATED

    if newly_launched:
        ARMA_PROCESS_EVER_SEEN = False
        ARMA_PROCESS_TERMINATED = False

    if ARMA_PROCESS_TERMINATED:  # If it is known the process has already terminated, don't iterate through processes
        return False

    is_process_running = utils.system_processes.program_running('arma3.exe', 'arma3_x64.exe')

    if is_process_running:
        ARMA_PROCESS_EVER_SEEN = True

    if ARMA_PROCESS_EVER_SEEN and not is_process_running:
        ARMA_PROCESS_TERMINATED = True
        return False

    return True
