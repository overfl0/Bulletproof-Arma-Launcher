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

# Allow relative imports when the script is run from the command line
if __name__ == "__main__":
    import site
    import os
    file_directory = os.path.dirname(os.path.realpath(__file__))
    site.addsitedir(os.path.abspath(os.path.join(file_directory, '..')))


import libtorrent
import os

from utils.metadatafile import MetadataFile
from time import sleep

class TorrentSyncer(object):
    _update_interval = 1
    _torrent_handle = None
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
        """Perform the initialization of things that should be initialized once"""
        settings = libtorrent.session_settings()
        settings.user_agent = 'TacBF (libtorrent/{})'.format(libtorrent.version)

        self.session = libtorrent.session()
        self.session.listen_on(6881, 6891)  # This is just a port suggestion. On failure, the port is automatically selected.

        # TODO: self.session.set_download_rate_limit(down_rate)
        # TODO: self.session.set_upload_rate_limit(up_rate)

        self.session.set_settings(settings)

    def get_torrent_info_from_string(self, bencoded):
        """Get torrent metadata from a bencoded string and return info structure."""

        torrent_metadata = libtorrent.bdecode(bencoded)
        torrent_info = libtorrent.torrent_info(torrent_metadata)

        return torrent_info

    def get_torrent_info_from_file(self, filename):
        """Get torrent_info structure from a file.
        The file should contain a bencoded string - the contents of a .torrent file."""

        with open(filename, 'rb') as file_handle:
            file_contents = file_handle.read()

            return self.get_torrent_info_from_string(file_contents)

    def get_session_logs(self):
        """Get alerts from torrent engine and forward them to the manager process"""
        torrent_log = []

        alerts = self.session.pop_alerts()  # Important: these are messages for the whole session, not only one torrent!
                                            # Use alert.handle in the future to get the torrent handle
        for alert in alerts:
            # Filter with: alert.category() & libtorrent.alert.category_t.error_notification
            print "Alerts: Category: {}, Message: {}".format(alert.category(), alert.message())
            torrent_log.append({'message': alert.message(), 'category': alert.category()})

        return torrent_log

    def sync(self):
        print "downloading ", self.mod.downloadurl, "to:", self.mod.clientlocation
        #TODO: Add the check: mod name == torrent directory name

        if not self.session:
            self.init_libtorrent()


        ### Metadata handling
        metadata_file = MetadataFile(os.path.join(self.mod.clientlocation, self.mod.name))
        metadata_file.read_data(ignore_open_errors=True)  # In case the mod does not exist, we would get an error

        metadata_file.set_dirty(True)  # Set as dirty in case this process is not terminated cleanly

        # If the torrent url changed, invalidate the resume data
        old_torrent_url = metadata_file.get_torrent_url()
        if old_torrent_url != self.mod.downloadurl:
            metadata_file.set_torrent_resume_data("")
            metadata_file.set_torrent_url(self.mod.downloadurl)

        metadata_file.write_data()
        # End of metadata handling


        ### Torrent parameters
        params = {
            'save_path': self.mod.clientlocation,
            'storage_mode': libtorrent.storage_mode_t.storage_mode_allocate,  # Reduce fragmentation on disk
        }

        # Configure torrent source
        if self.mod.downloadurl.startswith('file://'):  # Local torrent from file
            torrent_info = self.get_torrent_info_from_file(self.mod.downloadurl[len('file://'):])
            params['ti'] = torrent_info
        else:  # Torrent from url
            params['url'] = self.mod.downloadurl

        # Add optional resume data
        resume_data = metadata_file.get_torrent_resume_data()
        if resume_data:  # Quick resume torrent from data saved last time the torrent was run
            params['resume_data'] = resume_data

        # Launch the download of the torrent
        torrent_handle = self.session.add_torrent(params)
        self._torrent_handle = torrent_handle

        ### Main loop
        # Loop while the torrent is not completely downloaded
        while (not torrent_handle.is_seed()):
            s = torrent_handle.status()

            download_fraction = s.progress
            download_kbs = s.download_rate / 1024

            self.result_queue.progress({'msg': '[%s] %s: %.2f%%' % (self.mod.name, str(s.state), download_fraction * 100.0),
                                        'log': self.get_session_logs(),
                                       }, download_fraction)

            print '%.2f%% complete (down: %.1f kB/s up: %.1f kB/s peers: %d) %s' % \
                  (s.progress * 100, s.download_rate / 1024, s.upload_rate / 1024, s.num_peers, s.state)

            # TODO: Save resume_data periodically
            sleep(self._update_interval)

        #print torrent_handle.get_torrent_info()
        # Download finished. Performing housekeeping
        download_fraction = 1.0
        self.result_queue.progress({'msg': '[%s] %s' % (self.mod.name, torrent_handle.status().state),
                                    'log': self.get_session_logs(),
                                   }, download_fraction)


        # Save data that could come in handy in the future to a metadata file
        metadata_file.set_version(self.mod.version)
        metadata_file.set_dirty(False)

        # Set resume data for quick checksum check
        resume_data = libtorrent.bencode(torrent_handle.write_resume_data())
        metadata_file.set_torrent_resume_data(resume_data)

        metadata_file.write_data()


if __name__ == '__main__':
    class DummyMod:
        downloadurl = "https://archive.org/download/DebussyPrelduesBookI/DebussyPrelduesBookI_archive.torrent"
        #downloadurl = "file://test.torrent"
        clientlocation = ""
        name = "Prusa3-vanilla"
        version = "123"

    class DummyQueue:
        def progress(self, d, frac):
            print str(d)

    mod = DummyMod()
    queue = DummyQueue()

    ts = TorrentSyncer(queue, mod)
    ts.init_libtorrent()
    torrent_info = ts.get_torrent_info_from_file("test.torrent")

    num_files = torrent_info.num_files()
    print num_files

    ts.sync()
