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

import os

import kivy
import kivy.app  # To keep PyDev from complaining
import textwrap
from third_party.arma import Arma, ArmaNotInstalled, SteamNotInstalled
from gui.messagebox import MessageBox

from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image
from kivy.logger import Logger

from sync.modmanager import ModManager
from third_party import teamspeak
from utils.data.jsonstore import JsonStore
from utils.primitive_git import get_git_sha1_auto
from view.errorpopup import ErrorPopup, DEFAULT_ERROR_MESSAGE


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
        self.loading_gif = None
        self.mods = None
        self.arma_executable_object = None
        self.para = None

        # TODO: Maybe transform this into a state
        self.play_button_shown = False

        # Don't run logic if required third party programs are not installed
        if self.check_requirements(verbose=False):
            # download mod description
            self.para = self.mod_manager.download_mod_description()
            self.para.then(self.on_download_mod_description_resolve,
                           self.on_download_mod_description_reject,
                           self.on_download_mod_description_progress)

            Clock.schedule_interval(self.check_install_button, 0)
            Clock.schedule_interval(self.try_reenable_play_button, 1)

        else:
            # This will call check_requirements(dt) which is not really what we
            # want but it is good enough ;)
            Clock.schedule_interval(self.check_requirements, 1)

        Clock.schedule_once(self.update_footer_label, 0)

        # bind to application stop event
        application.bind(on_stop=self.on_application_stop)

    def try_reenable_play_button(self, dt):
        """This function first checks if a game process had been run. Then it checks
        if that process did terminate. If it did, the play button is reenabled
        """
        if self.arma_executable_object is None:
            return

        # TODO: Since we started to launch the game via steam.exe (as opposed to arma3battleye.exe)
        # the check below would only check if Steam has terminated on the first run (of steam)
        # On all subsequent runs steam terminates almost instantaneously (as an instance is already running.
        # Should probably check running processes for "arma3.exe" or something.
        # returncode = self.arma_executable_object.poll()
        # if returncode is None:  # The game has not terminated yet
        #     return

        # Logger.error('Arma has terminated with code: {}'.format(returncode))
        # Allow the game to be run once again.
        self.view.ids.install_button.disabled = False
        self.arma_executable_object = None

    def update_footer_label(self, dt):
        git_sha1 = get_git_sha1_auto()
        version = 'Alpha 6'
        footer_text = '{}\nBuild: {}'.format(version,
                                             git_sha1[:7] if git_sha1 else 'N/A')
        self.view.ids.footer_label.text = footer_text

    def check_install_button(self, dt):
        if 'install_button' in self.view.ids:
            self.on_install_button_ready()
            return False

    def try_enable_play_button(self):
        self.view.ids.install_button.disabled = True

        if not self.check_requirements(verbose=False):
            return

        if not self.mods:
            return

        for mod in self.mods:
            if not mod.up_to_date:
                return

        # switch to play button and a different handler
        self.view.ids.install_button.text = 'Play!'
        self.view.ids.install_button.bind(on_release=self.on_play_button_release)
        self.view.ids.install_button.disabled = False
        self.play_button_shown = True

    def check_requirements(self, verbose=True):
        """Check if all the required third party programs are installed in the system.
        Return True if the check passed.
        If verbose == true, show a message box in case of a failed check.
        """

        # TODO: move me to a better place
        try:
            teamspeak.check_installed()
        except teamspeak.TeamspeakNotInstalled:
            if verbose:
                message = """Teamspeak does not seem to be installed.
Having Teamspeak is required in order to play Tactical Battlefield.

[ref=https://www.teamspeak.com/downloads][color=3572b0]Get Teamspeak here.[/color][/ref]

Install Teamspeak and restart the launcher."""
                box = MessageBox(message, title='Teamspeak required!', markup=True)
                box.open()

            return False

        try:
            Arma.get_installation_path()
        except ArmaNotInstalled:
            if verbose:
                message = """Arma 3 does not seem to be installed.

Having Arma 3 is required in order to play Tactical Battlefield."""
                box = MessageBox(message, title='Arma 3 required!', markup=True)
                box.open()

            return False

        try:
            Arma.get_steam_exe_path()
        except SteamNotInstalled:
            if verbose:
                message = """Steam does not seem to be installed.
Having Steam is required in order to play Tactical Battlefield.

[ref=http://store.steampowered.com/about/][color=3572b0]Get Steam here.[/color][/ref]

Install Steam and restart the launcher."""
                box = MessageBox(message, title='Steam required!', markup=True)
                box.open()

            return False

        return True

    def on_install_button_ready(self):
        self.view.ids.install_button.text = 'Checking'
        self.view.ids.install_button.enable_progress_animation()

    def on_install_button_release(self, btn):
        # do nothing if sync was already resolved
        # this is a workaround because event is not unbindable, see
        # https://github.com/kivy/kivy/issues/903
        if self.play_button_shown:
            return

        self.view.ids.install_button.disabled = True
        self.para = self.mod_manager.sync_all()
        self.para.then(self.on_sync_resolve, self.on_sync_reject, self.on_sync_progress)
        self.view.ids.install_button.enable_progress_animation()

    # Download_mod_description callbacks #######################################

    def on_download_mod_description_progress(self, progress, speed):
        self.view.ids.status_image.hidden = False
        self.view.ids.status_label.text = progress['msg']

    def on_download_mod_description_resolve(self, progress):
        mod_description_data = progress['data']

        # Save mod_description_data to cache
        # FIXME: Why does this have to be so complicated? What is JsonStore
        # and why should I care? I should just have to do settings.set_sth() and
        # settings.save() and be done with it!
        settings = kivy.app.App.get_running_app().settings
        store = JsonStore(settings.config_path)
        settings.set_mod_data_cache(mod_description_data)
        store.save(settings.launcher_config)

        # Continue with processing mod_description data
        self.para = self.mod_manager.prepare_and_check(mod_description_data)
        self.para.then(self.on_checkmods_resolve,
                       self.on_checkmods_reject,
                       self.on_checkmods_progress)

    def on_download_mod_description_reject(self, data):
        # TODO: Move boilerplate code to a function
        # Boilerplate begin
        message = data.get('msg', DEFAULT_ERROR_MESSAGE)
        details = data.get('details', None)
        last_line = details if details else message
        last_line = last_line.rstrip().split('\n')[-1]

        # self.view.ids.install_button.disabled = False
        self.view.ids.status_image.hidden = True
        self.view.ids.status_label.text = last_line
        self.view.ids.install_button.disable_progress_animation()

        self.try_enable_play_button()
        # Boilerplate end

        # Ugly hack until we have an auto-updater
        if 'launcher is out of date' in message:
            message = textwrap.dedent('''
                This launcher is out of date!
                You won\'t be able do download mods until you update to the latest version!

                Get it here:

                [ref=https://bitbucket.org/tacbf_launcher/tacbf_launcher/downloads/tblauncher.exe][color=3572b0]https://bitbucket.org/tacbf_launcher/tacbf_launcher/downloads/tblauncher.exe[/color][/ref]
                ''')
            MessageBox(message, title='Get the new version of the launcher!', markup=True).open()
            return

        ErrorPopup(details=details, message=message).open()

        # Carry on with the execution! :)
        # Read data from cache and continue if successful
        settings = kivy.app.App.get_running_app().settings
        mod_data = settings.get_mod_data_cache()

        if mod_data:
            self.para = self.mod_manager.prepare_and_check(mod_data)
            self.para.then(self.on_checkmods_resolve,
                           self.on_checkmods_reject,
                           self.on_checkmods_progress)

    # Checkmods callbacks ######################################################

    def on_checkmods_progress(self, progress, speed):
        self.view.ids.status_image.hidden = False
        self.view.ids.status_label.text = progress['msg']

    def on_checkmods_resolve(self, progress):
        Logger.debug('InstallScreen: checking mods finished')
        self.view.ids.status_image.hidden = True
        self.view.ids.status_label.text = progress['msg']
        self.view.ids.install_button.disable_progress_animation()
        self.view.ids.install_button.text = 'Install'

        Logger.debug('InstallScreen: got mods:')
        for mod in progress['mods']:
            Logger.info('InstallScreen: {}'.format(mod))

        self.mods = progress['mods']
        self.try_enable_play_button()

        self.view.ids.install_button.disabled = False

    def on_checkmods_reject(self, data):
        message = data.get('msg', DEFAULT_ERROR_MESSAGE)
        details = data.get('details', None)
        last_line = details if details else message
        last_line = last_line.rstrip().split('\n')[-1]

        # self.view.ids.install_button.disabled = False
        self.view.ids.status_image.hidden = True
        self.view.ids.status_label.text = last_line
        self.view.ids.install_button.disable_progress_animation()

        self.try_enable_play_button()

        ErrorPopup(details=details, message=message).open()

    # Sync callbacks ###########################################################

    def on_sync_progress(self, progress, percentage):
        Logger.debug('InstallScreen: syncing in progress')
        self.view.ids.install_button.disabled = True
        self.view.ids.status_image.hidden = False
        self.view.ids.status_label.text = progress['msg']
        self.view.ids.progress_bar.value = percentage * 100

        message_box = progress.get('message_box')
        if message_box:
            message_box_instance = MessageBox(text=message_box['text'],
                                              title=message_box['title'],
                                              markup=message_box['markup'])
            message_box_instance.open()

    def on_sync_resolve(self, progress):
        Logger.info('InstallScreen: syncing finished')
        self.view.ids.install_button.disabled = False
        self.view.ids.status_image.hidden = True
        self.view.ids.status_label.text = progress['msg']
        self.view.ids.install_button.disable_progress_animation()

        self.try_enable_play_button()

    def on_sync_reject(self, data):
        Logger.info('InstallScreen: syncing failed')

        message = data.get('msg', DEFAULT_ERROR_MESSAGE)
        details = data.get('details', None)
        last_line = details if details else message
        last_line = last_line.rstrip().split('\n')[-1]

        self.view.ids.install_button.disabled = False
        self.view.ids.status_image.hidden = True
        self.view.ids.status_label.text = last_line
        self.view.ids.install_button.disable_progress_animation()

        self.try_enable_play_button()

        ErrorPopup(details=details, message=message).open()

    ############################################################################

    def on_play_button_release(self, btn):
        Logger.info('InstallScreen: User hit play')

        # TODO: Move all this logic somewhere else
        settings = kivy.app.App.get_running_app().settings
        mod_dir = settings.get_launcher_moddir()  # Why from there? This should be in mod.clientlocation but it isn't!

        mods_paths = []
        for mod in self.mods:
            mod_full_path = os.path.join(mod_dir, mod.foldername)
            mods_paths.append(mod_full_path)

        try:
            custom_args = []  # TODO: Make this user selectable
            self.arma_executable_object = Arma.run_game(mod_list=mods_paths, custom_args=custom_args)

        except ArmaNotInstalled:
            text = "Arma 3 does not seem to be installed."
            no_arma_info = MessageBox(text, title='Arma not installed!')
            no_arma_info.open()

        except SteamNotInstalled:
            text = "Steam does not seem to be installed."
            no_steam_info = MessageBox(text, title='Steam not installed!')
            no_steam_info.open()

        except OSError as ex:
            text = "Error while launching Arma 3: {}.".format(ex.strerror)
            error_info = MessageBox(text, title='Error while launching Arma 3!')
            error_info.open()

        self.view.ids.install_button.disabled = True

    def on_application_stop(self, something):
        Logger.info('InstallScreen: Application Stop, Trying to close child process')

        if self.para and self.para.is_open():
            self.para.request_termination()
            Logger.info("sending termination to para action {}".format(self.para.action_name))
        else:
            Logger.info("No open para. App can just close")
