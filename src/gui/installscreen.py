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

from multiprocessing import Queue

import kivy
import kivy.app  # To keep PyDev from complaining
import os
import textwrap
import third_party.helpers

from autoupdater import autoupdater
from config.version import version

from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image
from kivy.logger import Logger

from sync.modmanager import ModManager
from utils.primitive_git import get_git_sha1_auto
from utils.paths import is_pyinstaller_bundle
from view.errorpopup import ErrorPopup, DEFAULT_ERROR_MESSAGE
from view.messagebox import MessageBox


class InstallScreen(Screen):
    """
    View Class
    """
    def __init__(self, **kwargs):
        super(InstallScreen, self).__init__(**kwargs)
        self.controller = Controller(self)


class Controller(object):
    def __init__(self, widget):
        super(Controller, self).__init__()

        application = kivy.app.App.get_running_app()

        self.view = widget
        self.mod_manager = ModManager()
        self.settings = kivy.app.App.get_running_app().settings
        self.version = version

        self.start_mod_checking()

        Clock.schedule_once(self.update_footer_label, 0)

        # bind to application stop event
        application.bind(on_stop=self.on_application_stop)

        # bind to settings change
        self.settings.bind(on_change=self.on_settings_change)

    def start_mod_checking(self):
        """Start the whole process of getting metadata and then checking if all
        the mods are correctly downloaded.
        """

        self.para = None
        self.mods = []
        self.syncing_failed = False
        self.action_button_action = 'install'  # TODO: create an enum
        self.launcher = None

        # Don't run logic if required third party programs are not installed
        if third_party.helpers.check_requirements(verbose=False):
            # download mod description
            self.para = self.mod_manager.download_mod_description()
            self.para.then(self.on_download_mod_description_resolve,
                           self.on_download_mod_description_reject,
                           self.on_download_mod_description_progress)

            Clock.schedule_interval(self.wait_to_init_action_button, 0)
            Clock.schedule_interval(self.seeding_and_action_button_upkeep, 1)

        else:
            # This will check_requirements(dt) which is not really what we
            # want but it is good enough ;)
            Clock.schedule_interval(third_party.helpers.check_requirements, 1)

    def stop_mod_processing(self):
        """Forcefully stop any processing and ignore all the para promises.
        This is used to stop any running processes for restarting all the checks
        afterwards. (using wait_for_mod_checking_restart())
        """

        if self.para and self.para.is_open():
            # self.para.request_termination()
            self.para.request_termination_and_break_promises()

        Clock.unschedule(self.seeding_and_action_button_upkeep)
        Clock.unschedule(self.wait_to_init_action_button)

        self.view.ids.action_button.disable()

    def wait_for_mod_checking_restart(self, dt):
        """Scheduled method will wait until the para that is running is stopped
        and then restart the whole mod checking process.
        This is used when the mod directory has changed and everything needs to
        be done again, from the beginning.
        """

        if self.para and self.para.is_open():
            return  # Keep waiting

        self.start_mod_checking()

        return False  # Unschedule the method

    def seeding_and_action_button_upkeep(self, dt):
        """Check if seeding should be performed and if the play button should be available again.
        Start or stop seeding as needed.
        """

        # Check if we're ready to run the game - everything has been properly synced
        # TODO: use a state machine or anything else than comparing strings :(
        if self.view.ids.action_button.text != 'Play!':
            return

        arma_is_running = third_party.helpers.arma_may_be_running(newly_launched=False)

        # Start or stop seeding
        seeding_type = self.settings.get('seeding_type')

        # Check if seeding needs to stop
        if seeding_type == 'never' or \
           (seeding_type == 'while_not_playing' and arma_is_running):

            if self.para and self.para.is_open() and self.para.action_name == 'sync':
                Logger.info('Timer check: stopping seeding.')
                self.para.request_termination()

        # Check if seeding needs to start
        elif seeding_type == 'always' or \
                (seeding_type == 'while_not_playing' and not arma_is_running):
                    # Don't start if no mods, syncing failed or if it's already running
                    if self.mods and not self.para and not self.syncing_failed:
                        Logger.info('Timer check: starting seeding.')
                        self.start_syncing(seed=True)

        if not arma_is_running:
            # Allow the game to be run once again by enabling the play button.
            # Logger.info('Timer check: Re-enabling the Play button')
            self.view.ids.action_button.enable()

    def update_footer_label(self, dt):
        git_sha1 = get_git_sha1_auto()
        footer_text = 'Version: {}\nBuild: {}'.format(self.version,
                                                      git_sha1[:7] if git_sha1 else 'N/A')
        self.view.ids.footer_label.text = footer_text

    def wait_to_init_action_button(self, dt):
        if 'action_button' in self.view.ids:
            self.action_button_init()
            return False  # Return False to remove the callback from the scheduler

    def try_enable_play_button(self):
        """Enables or disables the action button (play, install, etc...).
        As a workaround, for now, returns False if administrator rights are
        required.
        """

        self.view.ids.action_button.disable()

        if is_pyinstaller_bundle() and self.launcher and autoupdater.should_update(
                u_from=self.version, u_to=self.launcher.version):

            launcher_executable = os.path.join(self.launcher.clientlocation, self.launcher.foldername, 'tblauncher.exe')
            same_files = autoupdater.compare_if_same_files(launcher_executable)

            # Safety check
            if self.launcher.up_to_date and same_files:
                Logger.error('Metadata says there is a newer version {} than our version {} but the files are the same. Aborting upgrade request.'
                             .format(self.launcher.version, self.version))

            else:
                # switch to play button and a different handler
                self.view.ids.action_button.text = 'Self-upgrade'
                self.action_button_action = 'self-upgrade'
                self.view.ids.action_button.enable()

                if autoupdater.require_admin_privileges():
                    self.view.ids.action_button.disable()
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

        for mod in self.mods:
            if not mod.up_to_date:
                return

        # switch to play button and a different handler
        self.view.ids.action_button.text = 'Play!'
        self.action_button_action = 'play'

        if not third_party.helpers.arma_may_be_running(newly_launched=False):
            self.view.ids.action_button.enable()

    def action_button_init(self):
        self.view.ids.action_button.text = 'Checking'
        self.view.ids.action_button.enable_progress_animation()

    def on_action_button_release(self, btn):
        # do nothing if sync was already resolved
        # this is a workaround because event is not unbindable, see
        # https://github.com/kivy/kivy/issues/903
        if self.action_button_action == 'play':
            return self.on_play_button_release(btn)
        elif self.action_button_action == 'self-upgrade':
            return self.on_self_upgrade_button_release(btn)

        # Else install everything
        self.start_syncing(seed=False)

    def start_syncing(self, seed=False):
        # Enable clicking on "play" button if we're just seeding
        if not seed:
            self.view.ids.action_button.disable()
            self.view.ids.action_button.enable_progress_animation()

        self.para = self.mod_manager.sync_all(seed=seed)
        self.para.then(self.on_sync_resolve, self.on_sync_reject, self.on_sync_progress)

    def on_self_upgrade_button_release(self, btn):
        self.view.ids.action_button.disable()
        self.para = self.mod_manager.sync_launcher()
        self.para.then(self.on_self_upgrade_resolve, self.on_sync_reject, self.on_sync_progress)
        self.view.ids.action_button.enable_progress_animation()

    def on_self_upgrade_resolve(self, data):
        # Terminate working paras here.
        if self.para and self.para.is_open():
            self.para.request_termination()
            Logger.info("sending termination to para action {}".format(self.para.action_name))

        # TODO: Parametrize name?
        executable = os.path.join(self.launcher.clientlocation, self.launcher.foldername, 'tblauncher.exe')
        autoupdater.request_my_update(executable)
        kivy.app.App.get_running_app().stop()

    # Download_mod_description callbacks #######################################

    def on_download_mod_description_progress(self, progress, speed):
        self.view.ids.status_image.show()
        self.view.ids.status_label.text = progress['msg']

    def on_download_mod_description_resolve(self, progress):
        self.para = None
        mod_description_data = progress['data']

        self.settings.set('mod_data_cache', mod_description_data)

        # Continue with processing mod_description data
        self.para = self.mod_manager.prepare_and_check(mod_description_data)
        self.para.then(self.on_checkmods_resolve,
                       self.on_checkmods_reject,
                       self.on_checkmods_progress)

    def on_download_mod_description_reject(self, data):
        self.para = None
        # TODO: Move boilerplate code to a function
        # Boilerplate begin
        message = data.get('msg', DEFAULT_ERROR_MESSAGE)
        details = data.get('details', None)
        last_line = details if details else message
        last_line = last_line.rstrip().split('\n')[-1]

        self.view.ids.status_image.set_image('attention')
        self.view.ids.status_label.text = last_line
        self.view.ids.action_button.disable_progress_animation()

        self.try_enable_play_button()
        # Boilerplate end

        # Ugly hack until we have an auto-updater
        if 'launcher is out of date' in message:
            message = textwrap.dedent('''
                This launcher is out of date!
                You won\'t be able to download mods until you update to the latest version!

                Get it here:

                [ref=https://bitbucket.org/tacbf_launcher/tacbf_launcher/downloads/tblauncher.exe][color=3572b0]https://bitbucket.org/tacbf_launcher/tacbf_launcher/downloads/tblauncher.exe[/color][/ref]
                ''')
            MessageBox(message, title='Get the new version of the launcher!', markup=True).chain_open()
            return

        # Carry on with the execution! :)
        # Read data from cache and continue if successful
        mod_data = self.settings.get('mod_data_cache')

        ErrorPopup(details=details, message=message).chain_open()

        if mod_data:
            ErrorPopup(message=textwrap.dedent('''
            The launcher could not download mod requirements from the server.

            Using cached data from the last time the launcher has been used.
            ''')).chain_open()

            self.para = self.mod_manager.prepare_and_check(mod_data)
            self.para.then(self.on_checkmods_resolve,
                           self.on_checkmods_reject,
                           self.on_checkmods_progress)

    # Checkmods callbacks ######################################################

    def on_checkmods_progress(self, progress, speed):
        self.view.ids.status_image.show()
        self.view.ids.status_label.text = progress['msg']

    def on_checkmods_resolve(self, progress):
        self.para = None
        Logger.debug('InstallScreen: checking mods finished')
        self.view.ids.status_image.hide()
        self.view.ids.status_label.text = progress['msg']
        self.view.ids.action_button.disable_progress_animation()
        self.view.ids.action_button.text = 'Install'

        self.launcher = progress['launcher']

        Logger.debug('InstallScreen: got mods:')
        for mod in progress['mods']:
            Logger.info('InstallScreen: {}'.format(mod))

        self.mods = progress['mods']
        if self.try_enable_play_button() is not False:
            self.view.ids.action_button.enable()

    def on_checkmods_reject(self, data):
        self.para = None
        message = data.get('msg', DEFAULT_ERROR_MESSAGE)
        details = data.get('details', None)
        last_line = details if details else message
        last_line = last_line.rstrip().split('\n')[-1]

        self.view.ids.status_image.hide()
        self.view.ids.status_label.text = last_line
        self.view.ids.action_button.disable_progress_animation()

        self.syncing_failed = True
        self.try_enable_play_button()

        ErrorPopup(details=details, message=message).chain_open()

    # Sync callbacks ###########################################################

    def on_tfr_action(self, msgbox_ignore_me):
        """A quickly done workaround for asking the user to click OK and carry
        on with TFR plugin installation.
        Feel free to refactor me :).
        """
        if self.para and self.para.is_open() and self.para.action_name == 'sync':
            Logger.info('InstallScreen: User acknowledged TFR installation. Sending continue command.')
            self.para.send_message('tfr_install_as_admin')

        return None  # Returning True would prevent the popup from being closed

    def on_sync_progress(self, progress, percentage):
        # Logger.debug('InstallScreen: syncing in progress')

        self.view.ids.status_image.show()
        self.view.ids.status_label.text = progress['msg']
        self.view.ids.progress_bar.value = percentage * 100

        tfr_request_action = progress.get('tfr_request_action')
        message_box = progress.get('message_box')
        if message_box:
            on_dismiss = None
            if tfr_request_action:
                on_dismiss = self.on_tfr_action

            message_box_instance = MessageBox(text=message_box['text'],
                                              title=message_box['title'],
                                              markup=message_box['markup'],
                                              on_dismiss=on_dismiss)
            message_box_instance.chain_open()

    def on_sync_resolve(self, progress):
        self.para = None
        Logger.info('InstallScreen: syncing finished')
        self.view.ids.status_image.hide()
        self.view.ids.status_label.text = progress['msg']
        self.view.ids.action_button.disable_progress_animation()

        self.try_enable_play_button()

    def on_sync_reject(self, data):
        self.para = None
        Logger.info('InstallScreen: syncing failed')

        message = data.get('msg', DEFAULT_ERROR_MESSAGE)
        details = data.get('details', None)
        last_line = details if details else message
        last_line = last_line.rstrip().split('\n')[-1]

        self.view.ids.status_image.hide()
        self.view.ids.status_label.text = last_line
        self.view.ids.action_button.disable_progress_animation()

        self.syncing_failed = True
        self.try_enable_play_button()

        ErrorPopup(details=details, message=message).chain_open()

    ############################################################################

    def on_play_button_release(self, btn):
        Logger.info('InstallScreen: User hit play')

        seeding_type = self.settings.get('seeding_type')

        # Stop seeding if not set to always seed
        if seeding_type != 'always':
            if self.para and self.para.is_open() and self.para.action_name == 'sync':
                self.para.request_termination()

        third_party.helpers.run_the_game(self.mods)
        self.view.ids.action_button.disable()

    def on_settings_change(self, instance, key, old_value, value):
        Logger.debug('InstallScreen: Setting changed: {} : {} -> {}'.format(
            key, old_value, value))

        # Settings to pass to the torrent_syncer
        if key in ('max_upload_speed', 'max_download_speed'):

            # If we are in the process of syncing things by torrent request an
            # update of its settings
            if self.para and self.para.is_open() and self.para.action_name == 'sync':
                Logger.debug('InstallScreen: Passing setting {}={} to syncing subprocess'.format(key, value))
                self.para.send_message('torrent_settings', {key: value})

        # Note: seeding is handled in seeding_and_action_button_upkeep()

        # Mod directory has changed. Restart all the checks from the beginning.
        if key == 'launcher_moddir':
            self.stop_mod_processing()
            Clock.schedule_interval(self.wait_for_mod_checking_restart, 0.2)

    def on_application_stop(self, something):
        Logger.info('InstallScreen: Application Stop, Trying to close child process')

        if self.para and self.para.is_open():
            self.para.request_termination()
            Logger.info("sending termination to para action {}".format(self.para.action_name))
        else:
            Logger.info("No open para. App can just close")
