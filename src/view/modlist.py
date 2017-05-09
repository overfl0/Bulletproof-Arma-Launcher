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

import launcher_config
import kivy.utils
import os
import kivy.app
import textwrap

from utils import paths

from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import ListProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.relativelayout import RelativeLayout
from sync import manager_functions
from sync.torrent_utils import path_can_be_a_mod, path_already_used_for_mod
from utils.unicode_helpers import casefold
from utils.paths import is_dir_writable
from utils.process import protected_para
from view.behaviors import HoverBehavior
from view.behaviors import BgcolorBehavior, BubbleBehavior
from view.errorpopup import ErrorPopup, DEFAULT_ERROR_MESSAGE
from view.filechooser import FileChooser


class HoverImage(HoverBehavior, BubbleBehavior, ButtonBehavior, Image):
    pass


class ModListEntry(BgcolorBehavior, RelativeLayout):
    icon_color = kivy.utils.get_color_from_hex(launcher_config.dominant_color)[:3] + [0.8]
    icon_highlight_color = list([4 * i for i in icon_color[:3]] + [0.8])

    def highlight_button(self, instance, over):
        # Todo: Move this to some ButtonHighlihtBehavior or something
        instance.color = self.icon_highlight_color if over else self.icon_color

    def on_reject(self, data):
        # #print 'on_reject', data
        self.on_manual_path(self.mod, self.mod.get_real_full_path())  # Keep the old path
        self.ids.status_image.opacity = 0
        ErrorPopup(details=data.get('details', None), message=data.get('msg', DEFAULT_ERROR_MESSAGE)).open()
        self.update_status()

    def on_resolve(self, new_path):
        self.on_manual_path(self.mod, new_path)

        # self.ids.status_image.source = paths.get_resources_path('images/checkmark2_white.png')
        self.ids.status_image.opacity = 0
        self.update_status()

    def set_new_path(self, new_path):
        # Set the loader icon for the time being
        self.ids.status_image.source = paths.get_resources_path('images/loader.zip')
        self.ids.status_image.opacity = 1
        self.ids.status_image.color = self.icon_color

        para = protected_para(
            manager_functions.symlink_mod, (self.mod.get_full_path(), new_path), 'symlink_mod',
            then=(self.on_resolve, self.on_reject, None)
        )

        # Need to assign to self or it is going to be garbage collected and
        # callbacks won't fire
        self.paras.append(para)

        # TODO: Disable the buttons for the time of the para working

    def select_success(self, path):
        Logger.info('Modlist: User selected the directory: {}'.format(path))

        if not os.path.isdir(path):
            return 'Not a directory or unreadable:\n{}'.format(path)

        if not is_dir_writable(path):
            return 'Directory {} is not writable'.format(path)

        # Prevent idiot-loops (seriously, people doing this are idiots!)
        already_used_by = path_already_used_for_mod(path, self.owner.all_existing_mods)
        settings = kivy.app.App.get_running_app().settings
        if not path_can_be_a_mod(path, settings.get('launcher_moddir')) or \
            (already_used_by and already_used_by != self.mod.foldername):
            message = textwrap.dedent('''
                Really???

                You're now selecting the location where {} is ALREADY installed and you've chosen:
                {}

                You realize that selecting that directory will cause EVERYTHING
                inside that is not part of that mod to be DELETED?

                Think twice next time!
            ''').format(self.mod.foldername, path)
            return message

        if casefold(path) == casefold(self.mod.get_full_path()):
            Logger.info('select_success: Selected directory is the current one. Ignoring...')
            return

        self.set_new_path(path)

    def select_dir(self, instance):
        self.p = FileChooser(self.mod.get_full_path(),
                             'Manually select {} location on your disk'.format(self.mod.foldername),
                             on_success=self.select_success)

    def update_status(self):
        if not os.path.isdir(self.mod.get_full_path()):
            self.ids.mod_location.text = 'Missing. Requires download'

        else:
            if self.mod.is_using_a_link():
                self.ids.mod_location.text = 'Link: ' + self.mod.get_real_full_path()

            else:
                self.ids.mod_location.text = 'Local copy'

    def set_mod_selection(self, selected):
        """Callback that is called when the user checks or unchecks the
        "selected" checkbox of a mod.
        """

        self.mod.selected = selected

        settings = kivy.app.App.get_running_app().settings
        selected_optional_mods = settings.get('selected_optional_mods')

        # We're using such a way of adding and removing elements to change
        # the ID of the object because otherwise settings.set won't notice
        # the change and won't save the data
        if selected:
            selected_optional_mods = selected_optional_mods + [self.mod.foldername]

        else:
            selected_optional_mods = \
                [v for v in selected_optional_mods if v != self.mod.foldername]

        settings.set('selected_optional_mods', selected_optional_mods)

        self.on_select(self.mod)

    def __init__(self, mod, on_manual_path, on_select, owner, *args, **kwargs):
        self.mod = mod
        self.on_manual_path = on_manual_path
        self.on_select = on_select
        self.owner = owner
        self.paras = []  # TODO: Move this to some para_manager
        super(ModListEntry, self).__init__(*args, **kwargs)

        self.update_status()

class ModList(BoxLayout):
    color_odd = ListProperty([0, 0, 0, 1])
    color_even = ListProperty([0, 0, 0, 1])

    def resize(self, *args):
        self.height = sum(child.height for child in self.children)
        # #print "Resizing modlist to:", self.height

    def add_mod(self, mod):
        self.modlist.append(mod)
        color = self.color_odd if len(self.modlist) % 2 else self.color_even

        boxentry = ModListEntry(bcolor=color,
                                mod=mod,
                                on_manual_path=self.set_mod_directory,
                                on_select=self.call_on_select,
                                owner=self)
        boxentry.bind(size=self.resize)
        self.add_widget(boxentry)

        self.resize()

    def clear_mods(self):
        self.modlist = []
        self.clear_widgets()
        self.resize()

    def set_mods(self, mods):
        self.clear_mods()
        self.add_mods(mods)

    def set_all_existing_mods(self, all_existing_mods):
        self.all_existing_mods = all_existing_mods

    def add_mods(self, mods):
        for mod in mods:
            self.add_mod(mod)

    def set_mod_directory(self, mod, new_path):
        if self.on_manual_path:
            self.on_manual_path(mod, new_path)

    def set_on_manual_path(self, on_manual_path):
        self.on_manual_path = on_manual_path

    def call_on_select(self, mod):
        if self.on_select:
            self.on_select(mod)

    def set_on_select(self, on_select):
        self.on_select = on_select

    def __init__(self, entries=None, on_manual_path=None, on_select=None, **kwargs):
        super(ModList, self).__init__(orientation='vertical', spacing=0, **kwargs)

        self.set_on_manual_path(on_manual_path)
        self.set_on_select(on_select)

        self.modlist = []
        self.all_existing_mods = []
        if entries is None:
            entries = []

#         import itertools
#         from sync.mod import Mod
#         def multiply(elements, number):
#             return itertools.islice(itertools.cycle(elements), number)
#         # second = '\n[i][size=10]Link: C:\\Some\\Directory\\Here\\Steam\\SteamApps\\Workshop\\Stuff[/size][/i]'
#         second = ''
#         entries = list(multiply([
#             Mod('@First' + second, parent_location=''),
#             Mod('@Second' + second, parent_location=''),
#             Mod('@Third' + second, parent_location=''),
#         ], 30))

        for entry in entries:
            self.add_mod(entry)


class ModListScrolled(ScrollView):

    directory_selection_callback = ObjectProperty(None)
    mod_selection_callback = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super(ModListScrolled, self).__init__(orientation='vertical', spacing=0, **kwargs)

        self.bind(directory_selection_callback=self.set_on_manual_path)
        self.bind(mod_selection_callback=self.set_on_select)

    def set_mods(self, mods):
        self.ids.mods_list_scrolled.set_mods(mods)

    def set_all_existing_mods(self, all_existing_mods):
        self.ids.mods_list_scrolled.set_all_existing_mods(all_existing_mods)

    def set_on_manual_path(self, instance, on_manual_path):
        self.ids.mods_list_scrolled.set_on_manual_path(on_manual_path)

    def set_on_select(self, instance, on_select):
        self.ids.mods_list_scrolled.set_on_select(on_select)

    def disable(self):
        self.disabled = True

    def enable(self):
        self.disabled = False
Builder.load_file('kv/modlist.kv')
