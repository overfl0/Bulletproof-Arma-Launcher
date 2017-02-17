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

from kivy.logger import Logger
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.label import Label
from sync import manager_functions
from sync.torrent_utils import path_can_be_a_mod
from utils.paths import is_dir_writable
from utils.process import protected_para
from view.behaviors import HoverBehavior
from view.behaviors import BgcolorBehavior, BubbleBehavior
from view.errorpopup import ErrorPopup, DEFAULT_ERROR_MESSAGE
from view.filechooser import FileChooser
from view.messagebox import MessageBox



class HoverImage(HoverBehavior, BubbleBehavior, ButtonBehavior, Image):
    pass


class ModListEntry(BgcolorBehavior, BoxLayout):

    icon_color = kivy.utils.get_color_from_hex(launcher_config.dominant_color)[:3] + [0.8]
    icon_highlight_color = list([4 * i for i in icon_color[:3]] + [0.8])

    def highlight_button(self, instance, over):
        # Todo: Move this to some ButtonHighlihtBehavior or something
        instance.color = self.icon_highlight_color if over else self.icon_color

    def on_reject(self, data):
        # #print 'on_reject', data
        ErrorPopup(details=data.get('details', None), message=data.get('msg', DEFAULT_ERROR_MESSAGE)).open()

    def on_resolve(self, new_path):
        # print 'on_resolve', new_path
        MessageBox('Selected the following directory for mod {}:\n{}'.format(self.mod.foldername, new_path)).open()
        self.on_manual_path(self.mod, new_path)

        self.status_image.source = paths.get_resources_path('images/checkmark2_white.png')

    def set_new_path(self, new_path):
        # Set the loader icon for the time being
        self.status_image.source = paths.get_resources_path('images/loader.zip')
        self.status_image.opacity = 1
        self.status_image.color = self.icon_color

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
        settings = kivy.app.App.get_running_app().settings
        if not path_can_be_a_mod(path, settings.get('launcher_moddir')):
            message = textwrap.dedent('''
                Really???

                You're now selecting the location where {} is ALREADY installed and you've chosen:
                {}

                You realize that selecting that directory will cause EVERYTHING
                in there to be DELETED (save for that mod contents)?

                Think twice next time!
            ''').format(self.mod.foldername, path)
            return message

        self.set_new_path(path)

    def select_dir(self, instance):
        self.p = FileChooser(self.mod.get_full_path(),
                             'Manually select {} location on your disk'.format(self.mod.foldername),
                             on_success=self.select_success)

    def __init__(self, mod, on_manual_path, **kwargs):
        self.mod = mod
        self.on_manual_path = on_manual_path
        self.paras = []  # TODO: Move this to some para_manager
        kwargs['size_hint_y'] = None
        kwargs['height'] = 26
        super(ModListEntry, self).__init__(**kwargs)

        entry = BoxLayout(spacing=10, padding=(20, 0))
        mod_name_label = Label(text=self.mod.foldername)

        self.status_image = HoverImage(opacity=0,
            size_hint=(None, None), size=(25, 25), anim_delay=0.05,
            source=paths.get_resources_path('images/checkmark2_white.png'))

        # up_to_date_text = 'Up to date' if mod.is_complete() else 'Requires update'
        folder_path = paths.get_resources_path('images/folder_white.png')
        folder = HoverImage(color=self.icon_color, bubble_text='Manually\nselect\nlocation', arrow_pos='bottom_mid', source=folder_path, size_hint=(None, None), size=(25, 25))
        folder.bind(mouse_hover=self.highlight_button)
        folder.bind(on_release=self.select_dir)

        entry.add_widget(mod_name_label)
        entry.add_widget(self.status_image)
        entry.add_widget(folder)
        self.add_widget(entry)


class ModList(BoxLayout):
    color_odd = [0.3, 0.3, 0.3, 0.3]
    color_even = [0.3, 0.3, 0.3, 0.8]

    def resize(self, *args):
        self.height = sum(child.height for child in self.children)
        # #print "Resizing modlist to:", self.height

    def add_mod(self, mod):
        self.modlist.append(mod)
        color = self.color_even if len(self.modlist) % 2 else self.color_odd

        boxentry = ModListEntry(bcolor=color, mod=mod, on_manual_path=self.set_mod_directory)
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

    def add_mods(self, mods):
        for mod in mods:
            self.add_mod(mod)

    def set_mod_directory(self, mod, new_path):
        if self.on_manual_path:
            self.on_manual_path(mod, new_path)

    def __init__(self, entries=None, on_manual_path=None, **kwargs):
        super(ModList, self).__init__(orientation='vertical', spacing=0, **kwargs)

        self.on_manual_path = on_manual_path

        self.modlist = []
        if entries is None:
            entries = []

        # import itertools
        # from sync.mod import Mod
        # def multiply(elements, number):
        #     return itertools.islice(itertools.cycle(elements), number)
        # entries = list(multiply([Mod('@First'), Mod('@Second'), Mod('@Third')], 30))

        for entry in entries:
            self.add_mod(entry)

