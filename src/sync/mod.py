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

class Mod(object):
    """encapsulate data needed for a mod"""
    def __init__(
            self,
            foldername='@noname',
            clientlocation=None,
            synctype='http',
            downloadurl=None,
            version=""):
        super(Mod, self).__init__()

        self.clientlocation = clientlocation
        self.synctype = synctype
        self.downloadurl = downloadurl
        self.foldername = foldername

    @classmethod
    def fromDict(cls, d):
        """return a new mod instance constructed from dictionary"""

        if 'version' in d:
            version = d['version']
        if 'name' in d:
            name = d['name']

        m = Mod(foldername=name, version=version)
        return m
