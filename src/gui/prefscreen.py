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

import os

import kivy
from kivy.clock import Clock

from kivy.uix.screenmanager import Screen
from kivy.logger import Logger

from view.filechooser import FileChooser
from utils.data.jsonstore import JsonStore


class PrefScreen(Screen):
    """
    View Class
    """
    def __init__(self, **kwargs):
        super(PrefScreen, self).__init__(**kwargs)
        self.controller = Controller(self)


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
        inputfield = self.view.ids.path_text_input
        inputfield.text = self.settings.get_launcher_basedir()

        return False

    def on_choose_path_button_release(self, btn):
        path = self.settings.get_launcher_basedir()

        Logger.info('opening filechooser with path: ' + path)

        p = FileChooser(select_string='Select', dirselect=True,
                        path=path)

        p.browser.bind(on_success=self._fbrowser_success,
                       on_canceled=self._fbrowser_canceled)
        p.open()
        self.file_browser_popup = p

    def _fbrowser_canceled(self, instance):
        print 'cancelled, Close self.'

    def _fbrowser_success(self, instance):
        if len(instance.selection) > 0:
            path = instance.selection[0]
        else:
            Logger.error('PrefScreen: no selection made')
            return False

        if not os.path.isdir(path):
            Logger.error('PrefScreen: path is not a dir: ' + path)
            return False

        Logger.info('PrefScreen: Got filechooser ok event: ' + path)
        store = JsonStore(self.settings.config_path)
        self.settings.set_launcher_basedir(path)
        store.save(self.settings.launcher_config)
        self.settings.reinit()
        # Fixme: Workaround: resave the settings in case something went wrong
        # with reinit and the paths have changed again
        store.save(self.settings.launcher_config)
        self.view.ids.path_text_input.text = self.settings.get_launcher_basedir()

        if self.file_browser_popup:
            self.file_browser_popup.dismiss()
