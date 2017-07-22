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

import os

import kivy
import kivy.app

from kivy.clock import Clock
from kivy.uix.screenmanager import Screen
from kivy.uix.gridlayout import GridLayout
from kivy.logger import Logger

from view.filechooser import FileChooser
from view.simplewidgets import Devmode_options
from utils.devmode import devmode
from utils.paths import is_dir_writable


class PrefScreen(Screen):
    """
    View Class
    """
    def __init__(self, **kwargs):
        super(PrefScreen, self).__init__(**kwargs)
        self.controller = Controller(self)

        if devmode.get_devmode_options():
            Clock.schedule_interval(self.enable_devmode_options, 1)

    def enable_devmode_options(self, *args):
        """Append additional options available only if set in devmode.
        The variable that needs to be set is: `devmode_options`.
        """

        try:
            # Try getting access to the widget we want to append to
            self.ids.arma_options.ids.scrollview_content
        except:
            return

        install_screen = self.manager.get_screen('install_screen')
        mod_manager = install_screen.controller.mod_manager

        devmode_options = Devmode_options(mod_manager)
        self.ids.arma_options.ids.scrollview_content.add_widget(devmode_options)

        # Return False to unschedule the function
        return False

class Controller(object):
    def __init__(self, widget):
        super(Controller, self).__init__()

        # dependencies
        self.view = widget
        self.settings = kivy.app.App.get_running_app().settings
        self.file_browser_popup = None

        Logger.info('PrefScreen: init controller')

        Clock.schedule_once(self.check_childs, 0)

    def check_childs(self, dt):
        inputfield = self.view.ids.mods_options.ids.path_text_input
        max_download_speed_input = self.view.ids.mods_options.ids.max_download_speed_input
        max_upload_speed_input = self.view.ids.mods_options.ids.max_upload_speed_input
        seedingtype_radios = [
            self.view.ids.mods_options.ids.sbox_while_not_playing,
            self.view.ids.mods_options.ids.sbox_never,
            self.view.ids.mods_options.ids.sbox_always
        ]

        # init path selection
        inputfield.text = self.settings.get('launcher_moddir')

        # init upload download inputs
        max_upload_speed_input.text = str(self.settings.get('max_upload_speed'))
        max_upload_speed_input.bind(
            focus=self.on_max_upload_speed_input_focus)
        max_download_speed_input.text = str(self.settings.get('max_download_speed'))
        max_download_speed_input.bind(
            focus=self.on_max_download_speed_input_focus)

        # init seedingtype
        Logger.debug('PrefScreen: got radio buttons: {}'.format(seedingtype_radios))
        for radio in seedingtype_radios:
            saved = self.settings.get('seeding_type')
            if radio.seeding_type == saved:
                radio.active = True
            radio.bind(active=self.on_radio_button_active)

        return False

    def on_choose_path_button_release(self, btn):
        path = self.settings.get('launcher_moddir')

        Logger.info('opening filechooser with path: ' + path)

        self.p = FileChooser(path,
                             on_success=self._fbrowser_success,
                             on_canceled=self._fbrowser_canceled)

    def _fbrowser_canceled(self):
        Logger.info('cancelled, Close self.')

    def _fbrowser_success(self, path):
        if not os.path.isdir(path):
            Logger.error('PrefScreen: path is not a dir: ' + path)
            return 'The selected path does not point to a directory'.format(path)

        if not is_dir_writable(path):
            Logger.error('PrefScreen: Directory {} is not writable'.format(path))
            return 'Directory {} is not writable'.format(path)

        # normalize path
        path = os.path.abspath(path)
        Logger.info('PrefScreen: Got filechooser ok event: ' + path)

        # this will save automatically
        self.settings.set('launcher_moddir', path)

        self.view.ids.mods_options.ids.path_text_input.text = self.settings.get('launcher_moddir')

    def on_max_download_speed_input_focus(self, numberinput, focus):
        if not focus:
            Logger.debug('max_download_speed_input unfocused')
            self.settings.set('max_download_speed', numberinput.get_value())

    def on_max_upload_speed_input_focus(self, numberinput, focus):
        if not focus:
            Logger.debug('max_upload_speed_input unfocused')
            self.settings.set('max_upload_speed', numberinput.get_value())

    def on_radio_button_active(self, radio_button, active):
        if active:
            self.settings.set('seeding_type', radio_button.seeding_type)

    def request_mods_recheck(self, *args, **kwargs):
        force_download_new = kwargs.get('force_download_new', False)
        install_screen = self.view.manager.get_screen('install_screen')
        install_screen.controller.restart_checking_mods(force_download_new=force_download_new)

    def disable_action_widgets(self):
        self.view.ids.mods_options.ids.mod_location_selection.disabled = True
        self.view.ids.mods_options.ids.mods_list.disable()

    def enable_action_widgets(self):
        self.view.ids.mods_options.ids.mod_location_selection.disabled = False
        self.view.ids.mods_options.ids.mods_list.enable()
