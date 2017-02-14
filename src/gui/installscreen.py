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

        def check_requirements_and_start():
            """This function is present because we have to somehow run code
            after the "arma_not_found_workaround" is run.
            """

            # Uncomment the code below to enable troubleshooting mode
            # Clock.schedule_once(third_party.helpers.check_requirements_troubleshooting, 0)
            # return

            # Don't run logic if required third party programs are not installed
            if third_party.helpers.check_requirements(verbose=False):
                # download mod description
                self.start_mod_checking()

            else:
                # This will check_requirements(dt) which is not really what we
                # want but it is good enough ;)
                Clock.schedule_once(third_party.helpers.check_requirements, 0.1)

        third_party.helpers.arma_not_found_workaround(on_ok=check_requirements_and_start,
                                                      on_error=check_requirements_and_start)

    def start_mod_checking(self):
        """Start the whole process of getting metadata and then checking if all
        the mods are correctly downloaded.
        """

        self.syncing_failed = False
        self.mod_manager.reset()

        # download mod description
        self.para = self.mod_manager.download_mod_description()
        self.para.then(self.on_download_mod_description_resolve,
                       self.on_download_mod_description_reject,
                       self.on_download_mod_description_progress)

        Clock.schedule_interval(self.wait_to_init_action_button, 0)
        Clock.schedule_interval(self.seeding_and_action_button_upkeep, 1)

    def is_para_running(self, name=None):
        """Check if a given para is now running or if any para is running in
        case no name is given.
        """

        if not self.para or not self.para.is_open():
            return False

        if name:
            return self.para.action_name == name
        else:
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
        Clock.unschedule(self.wait_to_init_action_button)

        self.disable_action_buttons()

    def wait_for_mod_checking_restart(self, dt):
        """Scheduled method will wait until the para that is running is stopped
        and then restart the whole mod checking process.
        This is used when the mod directory has changed and everything needs to
        be done again, from the beginning.
        """

        if self.is_para_running():
            return  # Keep waiting

        self.start_mod_checking()

        return False  # Unschedule the method

    def restart_checking_mods(self):
        """Request that any paras be stopped, and as soon as they are stopped,
        recheck all the mods again.
        """

        self.disable_action_buttons()
        self.stop_mod_processing()
        Clock.schedule_interval(self.wait_for_mod_checking_restart, 0.2)

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

        # Check if seeding needs to start
        elif seeding_type == 'always' or \
                (seeding_type == 'while_not_playing' and not arma_is_running):
                    # Don't start if no mods, syncing failed or if it's already running
                    if self.mod_manager.get_mods() and not self.para and not self.syncing_failed:
                        Logger.info('Timer check: starting seeding.')
                        self.start_syncing(seed=True)

        if not arma_is_running:
            # Allow the game to be run once again by enabling the play button.
            # Logger.info('Timer check: Re-enabling the Play button')
            self.enable_action_buttons()

    def update_footer_label(self, dt):
        git_sha1 = get_git_sha1_auto()
        footer_text = 'Version: {}\nBuild: {}'.format(self.version,
                                                      git_sha1[:7] if git_sha1 else 'N/A')
        self.view.ids.footer_label.text = footer_text.upper()

    def wait_to_init_action_button(self, dt):
        # self.view.width is normally set to 100 by default, it seems...
        if 'action_button' in self.view.ids and self.view.width != 100:
            self.action_button_init()
            self.disable_action_buttons()

            return False  # Return False to remove the callback from the scheduler

    def show_more_play_button(self):
        """Show the "more play options" button."""
        if not self.view.ids.more_play.custom_hidden:
            return
        self.view.ids.more_play.custom_hidden = False

        if self.view.ids.more_play.claim_space:
            self.view.ids.action_button.width = self.view.ids.action_button.width - self.view.ids.more_play.width

        self.view.ids.more_play.y = self.view.ids.action_button.y
        self.view.ids.more_play.x = self.view.ids.action_button.right

    def hide_more_play_button(self):
        """Hide the "more play options" button."""
        if self.view.ids.more_play.custom_hidden:
            return

        self.view.ids.more_play.custom_hidden = True
        self.view.ids.more_play.y = -5000

        if self.view.ids.more_play.claim_space:
            self.view.ids.action_button.width = self.view.ids.action_button.width + self.view.ids.more_play.width

    def enable_action_buttons(self):
        self.view.ids.more_play.enable()
        self.view.ids.action_button.enable()

    def disable_action_buttons(self):
        self.view.ids.more_play.disable()
        self.view.ids.action_button.disable()

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
                self.set_and_resize_action_button(DynamicButtonStates.self_upgrade)
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

        # TODO: Perform this check once, at the start of the launcher
        if not third_party.helpers.check_requirements(verbose=False):
            return

        for mod in self.mod_manager.get_mods():
            if not mod.is_complete():
                return

        # switch to play button and a different handler
        self.set_and_resize_action_button(DynamicButtonStates.play)

        if not third_party.helpers.arma_may_be_running(newly_launched=False):
            self.enable_action_buttons()

    def action_button_init(self):
        """Set all the callbacks for the dynamic action button."""

        button_states = [
            (DynamicButtonStates.play, 'PLAY', self.on_play_button_release),
            (DynamicButtonStates.checking, 'CHECKING...', None),
            (DynamicButtonStates.install, 'INSTALL', self.on_install_button_click),
            (DynamicButtonStates.self_upgrade, 'UPGRADE', self.on_self_upgrade_button_release)
        ]

        # Bind text and callbacks for button states
        for (name, text, callback) in button_states:
            self.view.ids.action_button.bind_state(name, text, callback)

        self.set_and_resize_action_button(DynamicButtonStates.checking)

    def set_and_resize_action_button(self, state):
        """Change the action and the text on a button. Then, resize that button
        and optionally show the more_play_button.
        """

        self.view.ids.action_button.set_button_state(state)

        # Place the more_actions_button at the right place
        if state != DynamicButtonStates.play and state != DynamicButtonStates.install:
            self.hide_more_play_button()
        else:
            self.show_more_play_button()

    def _set_status_label(self, main, secondary=None):
        self.view.ids.status_label.text = main.upper() if main else ''

        if not secondary:
            self.view.ids.status_box.text = ''
        else:
            if isinstance(secondary, basestring):
                self.view.ids.status_box.text = secondary
            else:
                self.view.ids.status_box.text = ' / '.join(secondary).replace('@', '')

    def set_selected_server(self, server_name):
        """Select a new server and check if all the newly required mods are up
        to date.
        """

        self.mod_manager.select_server(server_name)
        self.restart_checking_mods()

    def on_more_play_button_release(self, btn):
        """Allow the user to select optional ways to play the game."""

        button_state = self.view.ids.action_button.get_button_state()
        if button_state != DynamicButtonStates.play and button_state != DynamicButtonStates.install:
            Logger.error('Button more_action pressed when it should not be accessible!')
            return

        Logger.info('Opening GameSelectionBox')
        box = GameSelectionBox(self.set_selected_server, self.mod_manager.get_servers())
        box.open()

    def start_syncing(self, seed=False):
        # Enable clicking on "play" button if we're just seeding
        if not seed:
            self.disable_action_buttons()

        self.para = self.mod_manager.sync_all(seed=seed)
        self.para.then(self.on_sync_resolve, self.on_sync_reject, self.on_sync_progress)

    def on_prepare_resolve(self, progress):
        self.start_syncing(seed=False)

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

                message_box_instance = ModSearchBox(on_selection=self.on_prepare_search_decision,
                                                    on_manual_path=self.on_mod_set_path,
                                                    mods=mods,
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
        self.disable_action_buttons()

        self.para = self.mod_manager.prepare_all()
        self.para.then(self.on_prepare_resolve, self.on_sync_reject, self.on_prepare_progress)

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

        mods_to_convert = self.mod_manager.get_mods()[:]  # Work on the copy
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
        anim = Animation(width=label.width_final, right=label.right, t='in_out_circ')
        anim.bind(on_complete=partial(do_fade_in, result))
        anim.start(label)

        # Fix something that cannot be fixed in kv files
        label.ids.content.padding = 10, 0

    def on_download_mod_description_progress(self, progress, speed):
        self.view.ids.status_image.show()
        self._set_status_label(progress.get('msg'))

    def on_download_mod_description_resolve(self, data):
        # Continue with processing mod_description data
        self.checkmods(data['data'])

        if launcher_config.news_url:
            UrlRequest(launcher_config.news_url, on_success=partial(
                self.on_news_success, self.view.ids.news_label))

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
        Logger.debug('InstallScreen: checking mods finished')
        self.view.ids.status_image.hide()
        self._set_status_label(progress.get('msg'))
        self.view.ids.options_button.disabled = False
        self.disable_action_buttons()
        self.set_and_resize_action_button(DynamicButtonStates.install)

        if devmode.get_create_torrents(False):
            self.view.ids.make_torrent.enable()
            self.view.ids.make_torrent.text = 'CREATE'

        if self.try_enable_play_button() is not False:
            self.enable_action_buttons()

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

        ErrorPopup(details=details, message=message).chain_open()

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

        self.view.ids.status_image.show()
        self._set_status_label(progress.get('msg'), progress.get('mods'))
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
