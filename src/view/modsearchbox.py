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

import os

from kivy.lang import Builder
from kivy.uix.button import Button
from utils.paths import is_dir_writable
from view.chainedpopup import ChainedPopup
from view.behaviors import BubbleBehavior, HoverBehavior, DefaultButtonBehavior, HighlightBehavior
from view.filechooser import FileChooser

default_title = ''


class HButton(HighlightBehavior, HoverBehavior, BubbleBehavior, Button):
    pass


class DefaultHoverButton(HighlightBehavior, HoverBehavior, BubbleBehavior, DefaultButtonBehavior, Button):
    pass


Builder.load_file('kv/modsearchbox.kv')


class ModSearchBox(ChainedPopup):
    def resize_box(self, container, la, size):
        container.height = sum(child.height for child in container.children)

    def is_directory_ok(self, path):
        return os.path.isdir(path)

    def _fbrowser_success(self, path):
        if not self.is_directory_ok(path):
            return 'Not a directory or unreadable:\n{}'.format(path)

        if not is_dir_writable(path):
            return 'Directory {} is not writable'.format(path)

        self.dismiss()
        self.on_selection('search', path)

    def search_button_clicked(self, ignore):
        self.p = FileChooser(os.getcwd(),
                             'Select a location to search for all the missing mods at once.',
                             on_success=self._fbrowser_success)

    def ignore_button_clicked(self, ignore):
        self.dismiss()
        self.on_selection('download')

    def update_continue_button(self, *args):
        """Set button label to OK if all selected mods have a selected directory"""

        self.ids.continue_button.text = 'Download missing'

        for mod in self.mods:
            if mod.optional and not mod.selected:
                continue

            if not os.path.exists(mod.get_full_path()):
                return

        self.ids.continue_button.text = 'OK'

    def mod_location_selected(self, mod, new_path):
        if self.on_manual_path:
            self.on_manual_path(mod, new_path)

        self.update_continue_button()

    def mod_selected(self, mod):
        self.update_continue_button()

    def __init__(self, on_selection, on_manual_path, mods, all_existing_mods, title=default_title):
        self.mods = mods
        self.on_selection = on_selection
        self.on_manual_path = on_manual_path

        super(ModSearchBox, self).__init__(
            title=default_title, size_hint=(None, None), width=600, auto_dismiss=False)

        self.ids.modlist.set_all_existing_mods(all_existing_mods)
        self.ids.modlist.set_mods(mods)
        self.ids.modlist.set_on_manual_path(None, self.mod_location_selected)
        self.ids.modlist.set_on_select(None, self.mod_selected)
