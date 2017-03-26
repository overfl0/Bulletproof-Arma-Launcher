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

class Server(object):
    """Encapsulate data needed for a server"""

    def __init__(self, name, ip, port, password=None, teamspeak=None,
                 battleye=True, background=None):

        super(Server, self).__init__()

        self.name = name
        self.ip = ip
        self.port = port
        self.password = password
        self.teamspeak = teamspeak
        self.battleye = battleye
        self.mods = []
        self.selected = False
        self.background = background

    def add_mods(self, mods):
        """Add mods to a server.
        mods must be an array of Mod objects.
        """

        self.mods.extend(mods)

    def set_mods(self, mods):
        """Set mods for a server.
        mods must be an array of Mod objects.
        """

        self.mods = mods

    def get_mods(self):
        """Mods accessor."""
        return self.mods

    @staticmethod
    def fromDict(d):
        """Return a new server instance constructed from a dictionary"""

        name = d['name']
        ip = d['ip']
        port = d['port']
        password = d.get('password', None)
        teamspeak = d.get('teamspeak', None)
        battleye = d.get('battleye', True)
        background = d.get('background')

        server = Server(name=name, ip=ip, port=port, password=password,
                        teamspeak=teamspeak, battleye=battleye, background=background)

        return server

    def __repr__(self):
        mods_repr = ''
        if self.mods:
            mods_repr = '\n{}\n'.format('\n'.join('    ' + repr(mod) for mod in self.mods))

        s = '<Server: Name: {s.name}, IP: {s.ip}, Port: {s.port}, Battleye: {s.battleye}, Teamspeak: {s.teamspeak}, Background: {s.background}{}>'.format(
                mods_repr, s=self)

        return s
