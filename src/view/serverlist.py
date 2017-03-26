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
from sync.modmanager import ModManager
from sync.server import Server
from view.behaviors import HoverBehavior
from view.errorpopup import ErrorPopup, DEFAULT_ERROR_MESSAGE


class ServerListRefresh(BoxLayout):
    def __init__(self, owner, *args, **kwargs):
        super(ServerListRefresh, self).__init__(**kwargs)
        self.owner = owner

    def clicked(self, *args):
        self.owner.query_servers()

    def disable(self):
        self.ids.contents.disable()
        self.disabled = True

    def enable(self):
        self.ids.contents.enable()
        self.disabled = False


class ServerListEntry(BoxLayout):
    def __init__(self, server_list, server, *args, **kwargs):
        super(ServerListEntry, self).__init__(**kwargs)

        self.server_list = server_list
        self.server = server
        if self.server.name:
            self.ids.server_name.text = server.name

        else:
            self.ids.server_name.text = 'No server, just run Arma'

        if self.server.selected:
            self.select()

    def clicked(self, *args):
        # print 'Selected: ', self.server.name
        self.server_list.selection_changed(self)

    def select(self):
        self.ids.contents.force_hover = True

    def deselect(self):
        self.ids.contents.force_hover = False


class ServerListScrolled(ScrollView, HoverBehavior):

    selection_callback = ObjectProperty(None)
    servers = ListProperty()
    server_widgets = []

    def hover(self, *args):
        if self.refresh_widget:
            self.refresh_widget.opacity = int(self.mouse_hover)

    def __init__(self, *args, **kwargs):
        super(ServerListScrolled, self).__init__(**kwargs)

        self.bind(servers=self.set_servers)
        self.bind(mouse_hover=self.hover)
        self.para = None
        self.refresh_widget = None

    def on_query_servers_resolve(self, data):
        Logger.info('on_query_servers_resolve: {}'.format(data))
        self.para = None

        for server, widget, data in zip(self.servers, self.server_widgets, data.get('server_data', [])):
            widget.ids.server_players.text = data

            if server.selected:
                self.text = '{} ({})'.format(server.name, data)

        if self.refresh_widget:
            self.refresh_widget.enable()

    def on_query_servers_reject(self, data):
        Logger.info('on_query_servers_reject: {}'.format(data))
        self.para = None

        message = data.get('msg', DEFAULT_ERROR_MESSAGE)
        details = data.get('details', None)

        ErrorPopup(details=details, message=message).chain_open()

    def on_query_servers_progress(self, data, progress):
        Logger.info('on_query_servers_progress: {}'.format(data))

        for server, widget, data in zip(self.servers, self.server_widgets, data.get('server_data', [])):
            widget.ids.server_players.text = data

            if server.selected:
                self.text = '{} ({})'.format(server.name, data)

    def query_servers(self):
        if self.refresh_widget:
            self.refresh_widget.disable()

        # Clean up an older para
        if self.para:
            self.para.request_termination_and_break_promises()

        self.para = ModManager.query_servers((tuple(server for server in self.servers),))
        self.para.then(self.on_query_servers_resolve,
                       self.on_query_servers_reject,
                       self.on_query_servers_progress)

    def selection_changed(self, selected):
        for list_entry in self.server_widgets:
            if list_entry is selected:
                list_entry.select()
            else:
                list_entry.deselect()

        if self.selection_callback:
            self.selection_callback(selected.server.name)

    def set_servers(self, instance, servers):
        self.ids.servers_list.clear_widgets()
        self.server_widgets = []

        # Refresh widget
        self.refresh_widget = ServerListRefresh(self)
        self.ids.servers_list.add_widget(self.refresh_widget)

        # All the servers
        for server in self.servers:
            server_entry = ServerListEntry(self, server)
            self.server_widgets.append(server_entry)
            self.ids.servers_list.add_widget(server_entry)

        # Add the "just run Arma" entry
        dummy_server = Server(None, None, None)
        dummy_server.selected = not any(s.selected for s in  self.servers)
        dummy_server_entry = ServerListEntry(self, dummy_server)
        self.server_widgets.append(dummy_server_entry)
        self.ids.servers_list.add_widget(dummy_server_entry)

        # Check people on the servers
        self.query_servers()


Builder.load_file('kv/serverlist.kv')
