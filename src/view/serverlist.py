# Bulletproof Arma Launcher
# Copyright (C) 2017 Lukasz Taczuk
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


from kivy.lang import Builder
from kivy.logger import Logger
from kivy.properties import ListProperty, ObjectProperty
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from view.hoverbutton import HoverButton


class ServerListEntry(BoxLayout):
    def __init__(self, server_list, server, *args, **kwargs):
        super(ServerListEntry, self).__init__(**kwargs)

        self.server_list = server_list
        self.server = server
        self.ids.server_name.text = server.name

        if self.server.selected:
            self.select()

    def clicked(self, *args):
        print 'Selected: ', self.server.name
        self.server_list.selection_changed(self)

    def select(self):
        self.ids.contents.force_hover = True

    def deselect(self):
        self.ids.contents.force_hover = False

class ServerListScrolled(ScrollView):

    selection_callback = ObjectProperty(None)
    servers = ListProperty()
    server_widgets = []

    def __init__(self, *args, **kwargs):
        super(ServerListScrolled, self).__init__(**kwargs)

        self.bind(servers=self.set_servers)

    def selection_changed(self, selected):
        print "Selection changed"
        for list_entry in self.server_widgets:
            if list_entry is selected:
                list_entry.select()
            else:
                list_entry.deselect()

        if self.selection_callback:
            self.selection_callback(selected.server.name)

    def set_servers(self, instance, servers):
        print instance, servers

        self.ids.servers_list.clear_widgets()
        self.server_widgets = []

        for server in self.servers:
            server_entry = ServerListEntry(self, server)
            self.server_widgets.append(server_entry)
            self.ids.servers_list.add_widget(server_entry)

Builder.load_file('kv/serverlist.kv')
