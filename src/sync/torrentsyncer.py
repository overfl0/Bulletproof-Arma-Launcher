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

import libtorrent
import os
import shutil

from time import sleep

class TorrentSyncer(object):
    _update_interval = 1
    _torrent_handle = None
    torrent_metadata = None
    torrent_info = None
    session = None

    file_paths = set()
    dirs = set()
    top_dirs = set()

    def __init__(self, result_queue, mod):
        """
        constructor

        Args:
            result_queue: the queue object where you can push the dict in
            mod: a mod instance you should care about
        """
        super(TorrentSyncer, self).__init__()
        self.result_queue = result_queue
        self.mod = mod

    def init_libtorrent(self):
        settings = libtorrent.session_settings()
        settings.user_agent = 'TacBF (libtorrent/{})'.format(libtorrent.version)

        self.session = libtorrent.session()
        self.session.listen_on(6881, 6891)  # TODO: check if this is necessary (maybe rely on automatic port selection?)

        # TODO: self.session.set_download_rate_limit(down_rate)
        # TODO: self.session.set_upload_rate_limit(up_rate)

        self.session.set_settings(settings)

    def init_metadata_from_string(self, bencoded):
        """Initialize torrent metadata from a bencoded string."""

        self.torrent_metadata = libtorrent.bdecode(bencoded)
        self.torrent_info = libtorrent.torrent_info(self.torrent_metadata)

    def init_metadata_from_file(self, filename):
        """Initialize torrent metadata from a file."""
        with open(filename, 'rb') as file_handle:
            file_contents = file_handle.read()

            self.init_metadata_from_string(file_contents)

    def get_session_logs(self):
        # Get alerts from torrent engine and forward them to the manager process
        torrent_log = []

        alerts = self.session.pop_alerts()  #  Important: these are messages for the whole session, not only one torrent!
        for alert in alerts:
            # Filter with: alert.category() & libtorrent.alert.category_t.error_notification
            print "Alerts: Category: {}, Message: {}".format(alert.category(), alert.message())
            torrent_log.append({'message': alert.message(), 'category': alert.category()})

        return torrent_log

    def sync(self):
        print "downloading ", self.mod.downloadurl, "to:", self.mod.clientlocation

        if not self.session:
            self.init_libtorrent()

        self.init_metadata_from_file(self.mod.downloadurl)

        params = {
            'save_path': self.mod.clientlocation,
            'storage_mode': libtorrent.storage_mode_t.storage_mode_allocate,  # Reduce fragmentation on disk # TODO: check when does allocation take place to notify user.
            'ti': self.torrent_info
            # 'url': http://....torrent
        }
        torrent_handle = self.session.add_torrent(params)
        self._torrent_handle = torrent_handle

        #print "Is seed:", torrent_handle.is_seed()
        while (not torrent_handle.is_seed()):
            s = torrent_handle.status()

            download_fraction = s.progress
            download_kbs = s.download_rate / 1024

            state_str = ['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating']
            print '%.2f%% complete (down: %.1f kB/s up: %.1f kB/s peers: %d) %s' % \
                (s.progress * 100, s.download_rate / 1024, s.upload_rate / 1024, \
                s.num_peers, s.state)

            self.result_queue.progress({'msg': '[%s] %s: %.2f%%' % (self.mod.name, str(s.state), download_fraction * 100.0),
                                        'log': self.get_session_logs(),
                                       }, download_fraction)

            sleep(self._update_interval)

        #print "Torrent: DONE!"
        #print "Is seed:", torrent_handle.is_seed()
        #print "State:", s.state
        # TODO: make sure files have been fully checked before exiting
        self.result_queue.progress({'msg': '[%s] %s' % (self.mod.name, str(s.state)),
                                    'log': self.get_session_logs(),
                                   }, download_fraction)
        # self.result_queue.resolve({'msg': 'Downloading mod finished: ' + self.mod.name})


if __name__ == '__main__':
    class DummyMod:
        downloadurl = "test.torrent"
        clientlocation = ""
        name = "dummy_name"
    class DummyQueue:
        def progress(self, d, frac):
            print str(d)

    mod = DummyMod()
    queue = DummyQueue()

    ts = TorrentSyncer(queue, mod)
    ts.init_libtorrent()
    ts.init_metadata_from_file("test.torrent")

    num_files = ts.torrent_info.num_files()
    print num_files

    ts.sync()
