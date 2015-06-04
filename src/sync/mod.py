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
            torrent_timestamp="",
            name="",
            version="",
            up_to_date=False):
        super(Mod, self).__init__()

        self.clientlocation = clientlocation
        self.synctype = synctype
        self.downloadurl = downloadurl
        self.foldername = foldername
        self.torrent_timestamp = torrent_timestamp
        self.name = name
        self.version = version
        self.up_to_date = up_to_date

    @classmethod
    def fromDict(cls, d):
        """return a new mod instance constructed from dictionary"""

        torrent_timestamp = d.get('torrent-timestamp', "")
        name = d.get('name', "Unknown Mod")
        foldername = d.get('foldername', "@Unknown")
        downloadurl = d.get('downloadurl', "")

        m = Mod(foldername=foldername, torrent_timestamp=torrent_timestamp,
                name=name, downloadurl=downloadurl)
        return m

    def __repr__(self):
        s = '[Mod: {} -- utcts: {} -- {} -- durl: {}]'.format(self.foldername,
                self.torrent_timestamp, self.name, self.downloadurl)

        return s
