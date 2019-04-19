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

from multiprocessing import Queue

import launcher_config
import kivy.app  # To keep PyDev from complaining
import os
import textwrap
import third_party.helpers
import urllib
import utils.system_processes

from autoupdater import autoupdater
from launcher_config.version import version
from functools import partial

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.network.urlrequest import UrlRequest
from kivy.uix.screenmanager import Screen
from kivy.logger import Logger

from sync.modmanager import ModManager
from utils.devmode import devmode
from utils.fake_enum import enum
from utils.primitive_git import get_git_sha1_auto
from utils.paths import is_pyinstaller_bundle
from view.errorpopup import ErrorPopup, DEFAULT_ERROR_MESSAGE
from view.gameselectionbox import GameSelectionBox
from view.modreusebox import ModReuseBox
from view.modsearchbox import ModSearchBox
from view.messagebox import MessageBox


class InstallScreen(Screen):
    """
    View Class
    """
    def __init__(self, **kwargs):
        super(InstallScreen, self).__init__(**kwargs)
        self.controller = Controller(self)


DynamicButtonStates = enum('play', 'checking', 'install', 'self_upgrade')


class Controller(object):
    def __init__(self, widget):
        super(Controller, self).__init__()

        application = kivy.app.App.get_running_app()

        self.view = widget
        self.settings = kivy.app.App.get_running_app().settings
        self.mod_manager = ModManager(self.settings)
        self.version = version
        self.para = None

        Clock.schedule_once(self.update_footer_label, 0)

        # bind to application stop event
        application.bind(on_stop=self.on_application_stop)

        # bind to settings change
        self.settings.bind(on_change=self.on_settings_change)

        def stage2_check_requirements_and_start():
            """This function is present because we have to somehow run code
            after the "arma_not_found_workaround" is run.
            """

            # Uncomment the code below to enable troubleshooting mode
            # Clock.schedule_once(third_party.helpers.check_requirements_troubleshooting, 0)
            # return

            # Don't run logic if required third party programs are not installed
            if third_party.helpers.check_requirements(verbose=False):
                # download mod description
                self.start_mod_checking(force_download_new=True)

            else:
                # This will check_requirements(dt) which is not really what we
                # want but it is good enough ;)
                Clock.schedule_once(third_party.helpers.check_requirements, 0.1)

        def stage1_wait_to_init_action_button(call_next, dt):
            # self.view.width is normally set to 100 by default, it seems...
            if 'action_button' in self.view.ids and self.view.width != 100:
                self.action_button_init()
                self.disable_action_buttons()

                call_next()
                return False  # Return False to remove the callback from the scheduler

        # Call stage1 and stage2 functions asynchronously

        workaround_partial = partial(third_party.helpers.arma_not_found_workaround,
                                     on_ok=stage2_check_requirements_and_start,
                                     on_error=stage2_check_requirements_and_start)

        Clock.schedule_interval(partial(stage1_wait_to_init_action_button, workaround_partial), 0)

    def start_mod_checking(self, force_download_new=False):
        """Start the whole process of getting metadata and then checking if all
        the mods are correctly downloaded.
        """
        self.set_action_button_state(DynamicButtonStates.checking)

        self.syncing_failed = False
        self.mod_manager.reset()

        if force_download_new:
            # download mod description
            self.para = self.mod_manager.download_mod_description()
            self.para.then(self.on_download_mod_description_resolve,
                           self.on_download_mod_description_reject,
                           self.on_download_mod_description_progress)

        else:
            # Reuse the cached value
            self.on_download_mod_description_resolve({'data': self.settings.get('mod_data_cache')})

        Clock.schedule_interval(self.seeding_and_action_button_upkeep, 1)
        self.watchdog_reschedule(self.settings.get('mod_data_cache'))


    def is_para_running(self, name=None, not_name=None):
        """Check if a given para is now running or if any para is running in
        case no name is given.
        """

        if not self.para or not self.para.is_open():
            return False

        if name:
            return self.para.action_name == name

        if not_name:
            return self.para.action_name != name

        return True

    def stop_mod_processing(self):
        """Forcefully stop any processing and ignore all the para promises.
        This is used to stop any running processes for restarting all the checks
        afterwards. (using wait_for_mod_checking_restart())
        """

        if self.is_para_running():
            # self.para.request_termination()
            self.para.request_termination_and_break_promises()

        Clock.unschedule(self.seeding_and_action_button_upkeep)
        Clock.unschedule(self.metadata_watchdog)

        self.disable_action_buttons()

    def wait_for_mod_checking_restart(self, force_download_new, dt):
        """Scheduled method will wait until the para that is running is stopped
        and then restart the whole mod checking process.
        This is used when the mod directory has changed and everything needs to
        be done again, from the beginning.
        """

        if self.is_para_running():
            return  # Keep waiting

        self.start_mod_checking(force_download_new=force_download_new)

        return False  # Unschedule the method

    def restart_checking_mods(self, force_download_new=False):
        """Request that any paras be stopped, and as soon as they are stopped,
        recheck all the mods again.
        """

        self.disable_action_buttons()
        self.stop_mod_processing()
        Clock.schedule_interval(partial(self.wait_for_mod_checking_restart, force_download_new), 0.2)

    def watchdog_reschedule(self, data=None):
        """Schedule or reschedule the metadata watchdog."""

        Clock.unschedule(self.metadata_watchdog)

        refresh_interval = 60 * 10  # Default interval - 10 minutes

        # Get the refresh interval from the last metadata.json we got
        if data:
            new_refresh = int(data.get('refresh', refresh_interval))
            # print new_refresh

            if new_refresh >= 10:
                refresh_interval = new_refresh

        Logger.info('watchdog_reschedule: Scheduling check every {} seconds'.format(refresh_interval))

        Clock.schedule_interval(self.metadata_watchdog, refresh_interval)

    def watchdog_requirements(self):
        """The requirements for the watchdog to try fetch an updated
        metadata.json file.
        """

        arma_is_running = third_party.helpers.arma_may_be_running(newly_launched=False)
        if arma_is_running:
            return False

        if not self.is_para_running('sync'):
            return False

        return True

    def on_watchdog_metadata_fetch(self, data):
        Logger.debug('on_watchdog_metadata_fetch: Fetch completed.')

        if not self.watchdog_requirements():
            Logger.debug('on_watchdog_metadata_fetch: Requirements not met. Aborting.')
            return

        data = data['data']

        if data != self.settings.get('mod_data_cache'):
            Logger.info('on_watchdog_metadata_fetch: Data differs, restarting the checking routine.')
            self.settings.set('automatic_download', True)
            self.restart_checking_mods(force_download_new=True)

        else:
            Logger.debug('on_watchdog_metadata_fetch: Data is still the same. Not doing anything.')

    def metadata_watchdog(self, dt):
        """Check if the metadata has changed from the time it was last fetched.

        Only do this if:
        - Arma is NOT running
        - We are either installing or seeding
        """

        if not self.watchdog_requirements():
            Logger.debug('metadata_watchdog: Requirements not met.')
            return

        Logger.debug('metadata_watchdog: Requirements met proceeding with the download.')

        self.watchdog_para = self.mod_manager.download_mod_description(dry_run=True)
        self.watchdog_para.then(self.on_watchdog_metadata_fetch, None, None)

    def seeding_and_action_button_upkeep(self, dt):
        """Check if seeding should be performed and if the play button should be available again.
        Start or stop seeding as needed.
        """

        # Check if we're ready to run the game - everything has been properly synced
        if self.view.ids.action_button.get_button_state() != DynamicButtonStates.play:
            return

        arma_is_running = third_party.helpers.arma_may_be_running(newly_launched=False)

        # Start or stop seeding
        seeding_type = self.settings.get('seeding_type')

        # Check if seeding needs to stop
        if seeding_type == 'never' or \
           (seeding_type == 'while_not_playing' and arma_is_running):

            if self.is_para_running('sync'):
                Logger.info('Timer check: stopping seeding.')
                self.para.request_termination()

                # Enable preferences screen mods_list
                Logger.info('upkeep: Enabling mods list in preferences')
                self.enable_updated_settings_mods_list()

        # Check if seeding needs to start
        elif seeding_type == 'always' or \
                (seeding_type == 'while_not_playing' and not arma_is_running):
                    # Don't start if no mods, syncing failed or if it's already running
                    if not self.para and self.mod_manager.get_mods(only_selected=True) and not self.syncing_failed:
                        Logger.info('Timer check: starting seeding.')
                        self.start_syncing(seed=True)

                        # Disable preferences screen mods_list
                        Logger.info('upkeep: Disabling mods list in preferences')
                        self.disable_settings_mods_list()

        if not arma_is_running:
            # Allow the game to be run once again by enabling the play button.
            # Logger.info('Timer check: Re-enabling the Play button')
            self.enable_action_buttons()

        else:
            # This is a stupid Arma 3 bug workaround, which sometimes runs
            # The BI launcher instead of Arma 3. Who knows why...
            if not hasattr(self, 'arma3_launcher_workaround_show_once'):
                if utils.system_processes.program_running('arma3launcher.exe'):

                    self.arma3_launcher_workaround_show_once = True
                    message = textwrap.dedent('''
                        Uh, oh! Something went wrong!

                        Arma 3 was supposed to be run...
                        ...but Arma itself decided to run the Arma 3 launcher instead!

                        It's an Arma 3 bug. Close the Arma 3 launcher, restart this launcher
                        and try again.
                        ''')
                    ErrorPopup(message=message).chain_open()
                    return

    def update_footer_label(self, dt):
        git_sha1 = get_git_sha1_auto()
        footer_text = 'Version: {}\nBuild: {}'.format(self.version,
                                                      git_sha1[:7] if git_sha1 else 'N/A')
        self.view.ids.footer_label.text = footer_text.upper()

    def enable_updated_settings_mods_list(self):
        mods_list = self.view.manager.get_screen('pref_screen').ids.mods_options.ids.mods_list
        mods_list.enable()
        mods = self.mod_manager.get_mods()
        all_existing_mods = self.mod_manager.get_mods(include_all_servers=True)
        mods_list.set_all_existing_mods(all_existing_mods)
        mods_list.set_mods(mods)

    def disable_settings_mods_list(self):
        mods_list = self.view.manager.get_screen('pref_screen').ids.mods_options.ids.mods_list
        mods_list.disable()

    def fold_server_list_scrolled(self):
        folded_height = getattr(self.view.ids.server_list_scrolled, 'folded_height', None)

        if folded_height is not None:
            if self.view.ids.server_list_scrolled.max_height != folded_height:
                anim = Animation(max_height=folded_height, t='out_circ', duration=0.5)
                anim.start(self.view.ids.server_list_scrolled)


    def enable_action_buttons(self):
        if not self.view.ids.action_button.disabled:
            return

        self.view.ids.action_button.enable()
        self.view.ids.selected_server.disabled = False
        self.view.ids.server_list_scrolled.disabled = False
        self.fold_server_list_scrolled()

        pref_screen = self.view.manager.get_screen('pref_screen')
        pref_screen.controller.enable_action_widgets()

        if self.get_action_button_state() != DynamicButtonStates.self_upgrade:
            self.enable_updated_settings_mods_list()

    def action_button_enabled(self):
        return self.view.ids.action_button.disabled == False

    def disable_action_buttons(self):
        if self.view.ids.action_button.disabled:
            return

        self.view.ids.action_button.disable()
        self.view.ids.selected_server.disabled = True
        self.view.ids.server_list_scrolled.disabled = True
        self.fold_server_list_scrolled()

        pref_screen = self.view.manager.get_screen('pref_screen')
        pref_screen.controller.disable_action_widgets()

    def try_enable_play_button(self):
        """Enables or disables the action button (play, install, etc...).
        As a workaround, for now, returns False if administrator rights are
        required.
        """

        self.disable_action_buttons()

        launcher = self.mod_manager.get_launcher()
        if is_pyinstaller_bundle() and launcher and autoupdater.should_update(
                u_from=self.version, u_to=launcher.version):

            launcher_executable = os.path.join(launcher.parent_location, launcher.foldername, '{}.exe'.format(launcher_config.executable_name))
            same_files = autoupdater.compare_if_same_files(launcher_executable)

            # Safety check
            if launcher.is_complete() and same_files:
                Logger.error('Metadata says there is a newer version {} than our version {} but the files are the same. Aborting upgrade request.'
                             .format(launcher.version, self.version))

            else:
                # switch to play button and a different handler
                self.set_action_button_state(DynamicButtonStates.self_upgrade)
                self.enable_action_buttons()

                if autoupdater.require_admin_privileges():
                    self.disable_action_buttons()
                    message = textwrap.dedent('''
                    This launcher is out of date and needs to be updated but it does not have
                    the required permissions to create new files!


                    You need to perform one of the following actions:

                    1) Run the launcher as administrator.
                    2) Or move the launcher to another directory that does not require administrator
                    privileges to create files and run it again.
                    ''')
                    MessageBox(message, title='Administrator permissions required!', markup=True).chain_open()

                return False

        for mod in self.mod_manager.get_mods(only_selected=True):
            if not mod.is_complete():
                return

        # switch to play button and a different handler
        self._set_status_label('Ready to play')
        self.set_action_button_state(DynamicButtonStates.play)

        if not third_party.helpers.arma_may_be_running(newly_launched=False):
            self.enable_action_buttons()

    def action_button_init(self):
        """Set all the callbacks for the dynamic action button."""

        # This is a workaround because many people thought that INSTALL meant installing from scratch
        # So we only show INSTALL during the first install. Then we show UPDATE
        if self.settings.get('launcher_moddir') and os.path.exists(self.settings.get('launcher_moddir')):
            install_text = 'UPDATE'
        else:
            install_text = 'INSTALL'

        button_states = [
            (DynamicButtonStates.play, 'PLAY', self.on_play_button_release),
            (DynamicButtonStates.checking, 'CHECKING...', None),
            (DynamicButtonStates.install, install_text, self.on_install_button_click),
            (DynamicButtonStates.self_upgrade, 'UPGRADE', self.on_self_upgrade_button_release)
        ]

        # Bind text and callbacks for button states
        for (name, text, callback) in button_states:
            self.view.ids.action_button.bind_state(name, text, callback)

        self.set_action_button_state(DynamicButtonStates.checking)

    def set_action_button_state(self, state):
        """Change the action and the text on the action_button."""

        self.view.ids.action_button.set_button_state(state)

    def get_action_button_state(self):
        """Get the action_button state."""

        return self.view.ids.action_button.get_button_state()

    def _set_status_label(self, main, secondary=None):
        new_text = main if main else ''

        if launcher_config.capitalize_status:
            new_text = new_text.upper()

        self.view.ids.status_label.text = new_text

        if not secondary:
            self.view.ids.status_box.text = ''
        else:
            if isinstance(secondary, basestring):
                self.view.ids.status_box.text = secondary
            else:
                self.view.ids.status_box.text = ' / '.join(secondary).replace('@', '')

    def set_selected_server_message(self, server_name):
        """Set the server name message on the selected server label.
        If serve_name is None, the message NO SERVER SELECTED is printed.
        """

        selected_server = server_name if server_name else 'NO SERVER SELECTED'
        if 'selected_server' in self.view.ids:
            self.view.ids.selected_server.text = selected_server

    def set_selected_server(self, server_name):
        """Select a new server and check if all the newly required mods are up
        to date.
        """

        self.mod_manager.select_server(server_name)
        self.set_selected_server_message(server_name)
        self.restart_checking_mods()

    def on_selected_server_button_release(self, btn):
        """Allow the user to select optional ways to play the game."""

        button_state = self.view.ids.action_button.get_button_state()
        if button_state != DynamicButtonStates.play and button_state != DynamicButtonStates.install:
            Logger.error('Button selected_server pressed when it should not be accessible!')
            return

        unfolded_height = getattr(self.view.ids.server_list_scrolled, 'unfolded_height', None)
        if unfolded_height:
            folded_height = getattr(self.view.ids.server_list_scrolled, 'folded_height', 0)

            if self.view.ids.server_list_scrolled.max_height != folded_height:
                anim = Animation(max_height=folded_height, t='out_circ', duration=0.5)

            else:
                anim = Animation(max_height=unfolded_height, t='in_circ', duration=0.5)

            anim.start(self.view.ids.server_list_scrolled)

        return
        # TODO: Remove all of the code below at a later time

        Logger.info('Opening GameSelectionBox')
        box = GameSelectionBox(self.set_selected_server, self.mod_manager.get_servers())
        box.open()

    def start_syncing(self, seed=False):
        # Enable clicking on "play" button if we're just seeding
        if not seed:
            self.disable_action_buttons()

        self.para = self.mod_manager.sync_all(seed=seed)
        self.para.then(self.on_sync_resolve, self.on_sync_reject, self.on_sync_progress)

    def on_prepare_resolve(self, seed, progress):
        self.start_syncing(seed=seed)

    def on_prepare_progress(self, progress, percentage):
        self.view.ids.status_image.show()
        self._set_status_label(progress.get('msg'))
        self.view.ids.progress_bar.value = percentage * 100

        message = progress.get('special_message')
        if message:
            # Message handling mode:
            command = message.get('command')
            params = message.get('params')

            if command == 'missing_mods':
                mod_names = params
                mods = [mod for mod in self.mod_manager.get_mods() if mod.foldername in mod_names]
                all_existing_mods = self.mod_manager.get_mods(include_all_servers=True)

                message_box_instance = ModSearchBox(on_selection=self.on_prepare_search_decision,
                                                    on_manual_path=self.on_mod_set_path,
                                                    mods=mods,
                                                    all_existing_mods=all_existing_mods
                                                   )
                message_box_instance.chain_open()

            elif command == 'mod_found_action':
                message_box_instance = ModReuseBox(on_selection=self.on_mod_found_decision,
                                                   mod_name=params['mod_name'],
                                                   locations=params['locations'],
                                                   )
                message_box_instance.chain_open()

    def on_mod_set_path(self, mod, new_path):
        if self.is_para_running('prepare_all'):
            Logger.info('InstallScreen: Custom mod location has been selected for mod {}'.format(mod.foldername))

            params = {
                'mod_name': mod.foldername,
                'action': 'discard',
            }

            self.para.send_message('mod_reuse', params)

    def on_prepare_search_decision(self, action, location=None):
        """A quickly done workaround for telling the launcher what to do with
        missing mods.
        Feel free to refactor me :).
        """

        if self.is_para_running('prepare_all'):
            Logger.info('InstallScreen: User has made a decision about missing mods. Passing it to the subprocess.')
            Logger.debug('InstallScreen: Action: {}, Location: {}'.format(action, location))

            params = {
                'location': location,
                'action': action
            }

            self.para.send_message('mod_search', params)

        return None

    def on_install_button_click(self, btn):
        """Just start syncing the mods."""

        if self.get_action_button_state() != DynamicButtonStates.play:
            self.disable_action_buttons()

        self.para = self.mod_manager.prepare_all()
        self.para.then(partial(self.on_prepare_resolve, self.settings.get('automatic_seed')),
                       self.on_sync_reject,
                       self.on_prepare_progress)

    def on_self_upgrade_button_release(self, btn):
        self.disable_action_buttons()
        self.para = self.mod_manager.sync_launcher()
        self.para.then(self.on_self_upgrade_resolve, self.on_sync_reject, self.on_sync_progress)

    def on_self_upgrade_resolve(self, data):
        # Terminate working paras here.
        if self.is_para_running():
            self.para.request_termination()
            Logger.info("sending termination to para action {}".format(self.para.action_name))

        launcher = self.mod_manager.get_launcher()
        executable = os.path.join(launcher.parent_location, launcher.foldername, '{}.exe'.format(launcher_config.executable_name))
        autoupdater.request_my_update(executable)
        kivy.app.App.get_running_app().stop()

    def on_make_torrent_button_release(self, btn):
        if self.para:
            ErrorPopup(message='Stop seeding first!').chain_open()
            return

        self.disable_action_buttons()
        self.view.ids.make_torrent.disable()
        self.view.ids.status_image.show()
        self._set_status_label('Creating torrents...')

        mods_to_convert = self.mod_manager.get_mods(only_selected=True)[:]  # Work on the copy
        if self.mod_manager.get_launcher():
            mods_to_convert.append(self.mod_manager.get_launcher())

        self.para = self.mod_manager.make_torrent(mods=mods_to_convert)
        self.para.then(self.on_maketorrent_resolve,
                       self.on_maketorrent_reject,
                       self.on_maketorrent_progress)

    def on_maketorrent_progress(self, progress, _):
        self.view.ids.status_image.show()
        self._set_status_label(progress.get('msg'))

        def send_message_to_para(para_name, message_name, params, popup):
            if self.is_para_running(para_name):
                Logger.info('InstallScreen: Sending reply to the para')
                self.para.send_message(message_name, params)

        if progress.get('action') == 'msgbox':
            MessageBox(text=progress.get('msg'), auto_dismiss=False,
                       on_dismiss=partial(send_message_to_para, 'make_torrent', progress.get('name'), True)
                       ).chain_open()

    def on_maketorrent_resolve(self, progress):
        self.para = None
        self._set_status_label(progress.get('msg'))
        self.view.ids.make_torrent.enable()
        self.view.ids.status_image.hide()

        if progress.get('mods_created', 0) > 0:
            # Set the settings to start seeding ASAP and restart everything
            self.settings.set('automatic_seed', True)

            # Prevent the the seeding process to be shut down
            if self.settings.get('seeding_type') == 'never':
                self.settings.set('seeding_type', 'while_not_playing')

            self.restart_checking_mods(force_download_new=True)

    def on_maketorrent_reject(self, data):
        self.para = None

        message = data.get('msg', DEFAULT_ERROR_MESSAGE)
        details = data.get('details', None)
        last_line = details if details else message
        last_line = last_line.rstrip().split('\n')[-1]

        self.view.ids.status_image.hide()
        self._set_status_label(last_line)
        self.disable_action_buttons()

        ErrorPopup(details=details, message=message).chain_open()

    # Download_mod_description callbacks #######################################

    def on_news_success(self, label, request, result):
        # TODO: Move me to another file

        def do_fade_in(text, anim, wid):
            wid.text = text

            # Do a fade-in. `for` is just in case there would be more than 1 child
            for child in wid.children:
                child.opacity = 0

                # The empty first Animation acts as a simple delay
                anim = Animation(opacity=1)
                anim.start(child)

        # Animations: first show the empty background and then fade in the contents
        if getattr(label, 'direction', 'left') == 'right':
            anim = Animation(width=label.width_final, t='in_out_circ')
        else:
            anim = Animation(width=label.width_final, right=label.right, t='in_out_circ')

        anim.bind(on_complete=partial(do_fade_in, result))

        # Only animate if this is the first time we load the text
        if label.text:
            label.text = result
        else:
            anim.start(label)

        # Fix something that cannot be fixed in kv files
        label.ids.content.padding = 10, 0

    def on_download_mod_description_progress(self, progress, speed):
        self.view.ids.status_image.show()
        self._set_status_label(progress.get('msg'))

    def on_download_mod_description_resolve(self, data):
        # Continue with processing mod_description data
        self.checkmods(data['data'])
        self.watchdog_reschedule(data['data'])

        if launcher_config.news_url:
            UrlRequest(launcher_config.news_url, on_success=partial(
                self.on_news_success, self.view.ids.news_label))
        UrlRequest('http://launcherstats.frontline-mod.com/launcher?domain=' +
                   urllib.quote(launcher_config.domain))

    def on_download_mod_description_reject(self, data):
        self.para = None
        # TODO: Move boilerplate code to a function
        # Boilerplate begin
        message = data.get('msg', DEFAULT_ERROR_MESSAGE)
        details = data.get('details', None)
        last_line = details if details else message
        last_line = last_line.rstrip().split('\n')[-1]

        self.view.ids.status_image.set_image('attention')
        self._set_status_label(last_line)
        self.view.ids.options_button.disabled = False
        self.disable_action_buttons()

        # Boilerplate end

        # Ugly hack until we have an auto-updater
        if 'launcher is out of date' in message:
            message = textwrap.dedent('''
                This launcher is out of date!
                You won\'t be able to download mods until you update to the latest version!

                Get it here:

                [ref={}][color=3572b0]{}[/color][/ref]
                '''.format(launcher_config.original_url, launcher_config.original_url))
            MessageBox(message, title='Get the new version of the launcher!', markup=True).chain_open()
            return

        ErrorPopup(details=details, message=message).chain_open()

        # Carry on with the execution! :)
        # Read data from cache and continue if successful
        mod_data = self.settings.get('mod_data_cache')
        if mod_data:
            ErrorPopup(message=textwrap.dedent('''
            The launcher could not download mod requirements from the master server.

            Using cached data from the last time the launcher has been used.
            ''')).chain_open()

            self.checkmods(mod_data)

            if launcher_config.news_url:
                UrlRequest(launcher_config.news_url, on_success=partial(self.on_news_success, self.view.ids.news_label))

    # Checkmods callbacks ######################################################

    def checkmods(self, mod_data):
        self.para = self.mod_manager.prepare_and_check(mod_data)
        self.para.then(self.on_checkmods_resolve,
                       self.on_checkmods_reject,
                       self.on_checkmods_progress)

    def on_checkmods_progress(self, progress, speed):
        self.view.ids.status_image.show()
        self._set_status_label(progress.get('msg'))

    def on_checkmods_resolve(self, progress):
        self.para = None
        Logger.debug('InstallScreen: Checking mods finished')
        self.view.ids.status_image.hide()
        self._set_status_label(progress.get('msg'))
        self.view.ids.options_button.disabled = False
        self.disable_action_buttons()
        self.set_action_button_state(DynamicButtonStates.install)

        if devmode.get_create_torrents(False):
            self.view.ids.make_torrent.enable()
            self.view.ids.make_torrent.text = 'CREATE'

        # Select the server for the mods
        try:
            selected_server = self.settings.get('selected_server')
            if selected_server is False:
                selected_server = self.mod_manager.select_first_server_available()
            else:
                self.mod_manager.select_server(selected_server)

        except KeyError:
            message = textwrap.dedent('''
                The server you selected previously is not available anymore:
                {}

                The first server from the servers list has been automatically
                selected. To change that, click the server name.
            ''').format(self.settings.get('selected_server'))
            MessageBox(text=message).chain_open()

            self.mod_manager.select_first_server_available()

        server = self.mod_manager.get_selected_server()

        main_widget = kivy.app.App.get_running_app().main_widget
        main_widget.controller.set_background(server.background if server else None)

        if self.try_enable_play_button() is not False:
            self.enable_action_buttons()

        if self.get_action_button_state() != DynamicButtonStates.self_upgrade:
            # Set server name label
            server_name = self.settings.get('selected_server')
            self.set_selected_server_message(server_name)

            self.view.ids.server_list_scrolled.servers = self.mod_manager.get_servers()
            self.fold_server_list_scrolled()

        if self.action_button_enabled() and self.get_action_button_state() == DynamicButtonStates.install:
            self._set_status_label('You need to install or update mods. Your existing mods will be autodetected!')

        # Automatic launching of scheduled one-time actions
        if self.action_button_enabled():
            if self.get_action_button_state() == DynamicButtonStates.install and \
                self.settings.get('automatic_download') or self.settings.get('automatic_seed'):
                    self.on_install_button_click(None)

            elif self.get_action_button_state() == DynamicButtonStates.play and \
                self.settings.get('automatic_seed'):
                    self.on_install_button_click(None)

        else:
            # Safety check
            if self.settings.get('automatic_download'):
                Logger.error('on_checkmods_resolve: Automatic download scheduled but button not enabled. Removing...')

            if self.settings.get('automatic_seed'):
                Logger.error('on_checkmods_resolve: Automatic seed scheduled but button not enabled. Removing...')

        # Reset the flags
        self.settings.set('automatic_download', False)
        self.settings.set('automatic_seed', False)

    def on_checkmods_reject(self, data):
        self.para = None
        message = data.get('msg', DEFAULT_ERROR_MESSAGE)
        details = data.get('details', None)
        last_line = details if details else message
        last_line = last_line.rstrip().split('\n')[-1]

        self.view.ids.status_image.hide()
        self._set_status_label(last_line)
        self.view.ids.options_button.disabled = False
        self.disable_action_buttons()

        self.syncing_failed = True
        # self.try_enable_play_button()

        ErrorPopup(details=details, message=message, auto_dismiss=False).chain_open()

    # Sync callbacks ###########################################################

    def on_tsplugin_action(self, msgbox_ignore_me):
        """A quickly done workaround for asking the user to click OK and carry
        on with a TS plugin installation.
        Feel free to refactor me :).
        """
        if self.is_para_running('sync'):
            Logger.info('InstallScreen: User acknowledged TS pluing installation. Sending continue command.')
            self.para.send_message('tsplugin_install_as_admin')

        return None  # Returning True would prevent the popup from being closed

    def on_mod_found_decision(self, mod_name, location, action):
        """A quickly done workaround for telling the launcher what to do with
        a mod found on disk.
        Feel free to refactor me :).
        """
        if self.is_para_running('prepare_all'):
            Logger.info('InstallScreen: User has made a decision about mod {}. Passing it to the subprocess.'.format(mod_name))
            Logger.debug('InstallScreen: Mod: {}, Location: {}, Action: {}'.format(mod_name, location, action))

            params = {
                'mod_name': mod_name,
                'location': location,
                'action': action
            }

            self.para.send_message('mod_reuse', params)

        return None

    def on_sync_progress(self, progress, percentage):
        # Logger.debug('InstallScreen: syncing in progress')

        # Hide the status indicator when we are seeding because that was somehow confusing people :(
        if percentage != 1:
            self.view.ids.status_image.show()
        else:
            self.view.ids.status_image.hide()
        self._set_status_label(progress.get('msg'), progress.get('mods'))

        # By request: show an empty progress bar if seeding (progress == 100%)
        if percentage == 1:
            percentage = 0

        self.view.ids.progress_bar.value = percentage * 100

        tsplugin_request_action = progress.get('tsplugin_request_action')
        message_box = progress.get('message_box')
        if message_box:
            on_dismiss = None
            if tsplugin_request_action:
                on_dismiss = self.on_tsplugin_action

            message_box_instance = MessageBox(text=message_box['text'],
                                              title=message_box['title'],
                                              markup=message_box['markup'],
                                              on_dismiss=on_dismiss)
            message_box_instance.chain_open()

    def on_sync_resolve(self, progress):
        self.para = None
        Logger.info('InstallScreen: syncing finished')
        self.view.ids.status_image.hide()
        self._set_status_label(progress.get('msg'))
        self.disable_action_buttons()

        self.try_enable_play_button()

    def on_sync_reject(self, data):
        self.para = None
        Logger.info('InstallScreen: syncing failed')

        message = data.get('msg', DEFAULT_ERROR_MESSAGE)
        details = data.get('details', None)
        last_line = details if details else message
        last_line = last_line.rstrip().split('\n')[-1]

        self.view.ids.status_image.hide()
        self._set_status_label(last_line)
        self.disable_action_buttons()

        self.syncing_failed = True
        # self.try_enable_play_button()
        Logger.info('InstallScreen: syncing failed. Enabling the install button to allow installing again.')
        self.enable_action_buttons()

        ErrorPopup(details=details, message=message).chain_open()

    ############################################################################

    def on_play_button_release(self, btn):
        Logger.info('InstallScreen: User hit play')

        if utils.system_processes.program_running('arma3launcher.exe'):
            ErrorPopup(message='Close Bohemia Interactive Arma 3 Launcher first!').chain_open()
            return

        seeding_type = self.settings.get('seeding_type')

        # Stop seeding if not set to always seed
        if seeding_type != 'always':
            if self.is_para_running('sync'):
                self.para.request_termination()

        self.mod_manager.run_the_game()
        self.disable_action_buttons()

    def on_settings_change(self, instance, key, old_value, value):
        Logger.debug('InstallScreen: Setting changed: {} : {} -> {}'.format(
            key, old_value, value))

        # Settings to pass to the torrent_syncer
        if key in ('max_upload_speed', 'max_download_speed'):

            # If we are in the process of syncing things by torrent request an
            # update of its settings
            if self.is_para_running('sync'):
                Logger.debug('InstallScreen: Passing setting {}={} to syncing subprocess'.format(key, value))
                self.para.send_message('torrent_settings', {key: value})

        # Note: seeding is handled in seeding_and_action_button_upkeep()

        # Mod directory has changed. Restart all the checks from the beginning.
        if key == 'launcher_moddir':
            self.restart_checking_mods()

    def on_application_stop(self, something):
        Logger.info('InstallScreen: Application Stop, Trying to close child process')

        if self.is_para_running():
            self.para.request_termination()
            Logger.info("sending termination to para action {}".format(self.para.action_name))
        else:
            Logger.info("No open para. App can just close")

    def _get_pref_screen(self):
        """Helper to get the preference screen view."""
        return self.view.manager.get_screen('pref_screen').ids
