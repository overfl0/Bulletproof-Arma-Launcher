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

from __future__ import unicode_literals
# Note: every std::string coming from libtorrent should be decoded from utf-8
# like that: alert.message().decode('utf-8')
# Every string submitted to libtorrent should be encoded to utf-8 as well
# http://sourceforge.net/p/libtorrent/mailman/message/33684047/

# Allow relative imports when the script is run from the command line
if __name__ == "__main__":
    import site
    import os
    file_directory = os.path.dirname(os.path.realpath(__file__))
    site.addsitedir(os.path.abspath(os.path.join(file_directory, '..')))


import libtorrent
import os
import torrent_utils

from kivy.logger import Logger
from sync.integrity import check_mod_directories
from utils.metadatafile import MetadataFile
from utils.unicode_helpers import decode_utf8, encode_utf8
from time import sleep


class TorrentSyncer(object):
    _update_interval = 1
    session = None

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
        self.force_termination = False

    def init_libtorrent(self):
        """Perform the initialization of things that should be initialized once"""
        settings = libtorrent.session_settings()
        settings.user_agent = encode_utf8('TacBF (libtorrent/{})'.format(decode_utf8(libtorrent.version)))
        """When running on a network where the bandwidth is in such an abundance
        that it's virtually infinite, this algorithm is no longer necessary, and
        might even be harmful to throughput. It is adviced to experiment with the
        session_setting::mixed_mode_algorithm, setting it to session_settings::prefer_tcp.
        This setting entirely disables the balancing and unthrottles all connections."""
        settings.mixed_mode_algorithm = 0

        # Fingerprint = 'LT1080' == LibTorrent 1.0.8.0
        fingerprint = libtorrent.fingerprint(b'LT', *(int(i) for i in libtorrent.version.split('.')))

        self.session = libtorrent.session(fingerprint=fingerprint)
        self.session.listen_on(6881, 6891)  # This is just a port suggestion. On failure, the port is automatically selected.

        # TODO: self.session.set_download_rate_limit(down_rate)
        # TODO: self.session.set_upload_rate_limit(up_rate)

        self.session.set_settings(settings)

    def get_session_logs(self):
        """Get alerts from torrent engine and forward them to the manager process"""
        torrent_log = []

        alerts = self.session.pop_alerts()  # Important: these are messages for the whole session, not only one torrent!
                                            # Use alert.handle in the future to get the torrent handle
        for alert in alerts:
            # Filter with: alert.category() & libtorrent.alert.category_t.error_notification
            message = decode_utf8(alert.message())
            Logger.info("Alerts: Category: {}, Message: {}".format(alert.category(), message))
            torrent_log.append({'message': message, 'category': alert.category()})

        return torrent_log

    def handle_torrent_progress(self, s):
        """Just log the download progress for now."""
        download_fraction = s.progress
        download_kBps = s.download_rate / 1024
        upload_kBps = s.upload_rate / 1024
        state = decode_utf8(s.state.name)

        progress_message = '[{}] {}: {:0.2f}% ({:0.2f} KB/s)'.format(
                           self.mod.foldername, state, download_fraction * 100.0,
                           download_kBps)
        self.result_queue.progress({'msg': progress_message,
                                    'log': self.get_session_logs(),
                                    }, download_fraction)

        Logger.debug('%.2f%% complete (down: %.1f kB/s up: %.1f kB/s peers: %d) %s' %
                     (s.progress * 100, download_kBps, upload_kBps, s.num_peers, state))

    def start_syncing(self, mod, force_sync=False):
        Logger.info('Downloading {} to {}'.format(mod.downloadurl, mod.clientlocation))
        # TODO: Add the check: mod name == torrent directory name

        # === Metadata handling ===
        metadata_file = MetadataFile(os.path.join(mod.clientlocation, mod.foldername))
        metadata_file.read_data(ignore_open_errors=True)  # In case the mod does not exist, we would get an error

        metadata_file.set_dirty(True)  # Set as dirty in case this process is not terminated cleanly

        # If the torrent url changed, invalidate the resume data
        old_torrent_url = metadata_file.get_torrent_url()
        if old_torrent_url != mod.downloadurl or force_sync:
            metadata_file.set_torrent_resume_data("")
            metadata_file.set_torrent_url(mod.downloadurl)

        metadata_file.write_data()
        # End of metadata handling

        # === Torrent parameters ===
        params = {
            'save_path': encode_utf8(mod.clientlocation),
            'storage_mode': libtorrent.storage_mode_t.storage_mode_allocate,  # Reduce fragmentation on disk
            'flags': torrent_utils.create_add_torrent_flags()
        }

        # Configure torrent source
        if mod.downloadurl.startswith('file://'):  # Local torrent from file
            torrent_info = self.get_torrent_info_from_file(mod.downloadurl[len('file://'):])
            params['ti'] = torrent_info
        else:  # Torrent from url
            params['url'] = encode_utf8(mod.downloadurl)

        # Add optional resume data
        resume_data = metadata_file.get_torrent_resume_data()
        if resume_data:  # Quick resume torrent from data saved last time the torrent was run
            params['resume_data'] = resume_data

        # Launch the download of the torrent
        torrent_handle = self.session.add_torrent(params)
        return torrent_handle

    def sync(self, force_sync=False):
        """
        Synchronize the mod directory contents to contain exactly the files that
        are described in the torrent file.

        force_sync - Assume no resume data is available. Manually recheck all the
                     checksums for all the files in the torrent description.
        """

        if not self.session:
            self.init_libtorrent()

        torrent_handle = self.start_syncing(self.mod, force_sync)

        # === Main loop ===
        # Loop while the torrent is not completely downloaded
        finished_downloading = False
        s = torrent_handle.status()

        # Loop until finished and paused
        while not (finished_downloading and torrent_handle.is_paused()):
            if s.error:
                break

            # We are cancelling the downloads
            if self.result_queue.wants_termination():
                Logger.info('TorrentSyncer wants termination')
                self.force_termination = True

            # If finished downloading, request pausing the torrent to synchronize data to disk
            if (torrent_handle.is_seed() or self.force_termination) and not finished_downloading:
                finished_downloading = True

                # Stop the torrent to force syncing everything to disk
                Logger.info('Sync: pausing torrent')
                torrent_handle.auto_managed(False)
                torrent_handle.pause()

            self.handle_torrent_progress(s)

            # TODO: Save resume_data periodically
            sleep(self._update_interval)
            s = torrent_handle.status()

        self.handle_torrent_progress(s)

        Logger.info('Sync: terminated loop')

        if s.error:
            self.result_queue.reject({'details': 'An error occured: Libtorrent error: {}'.format(decode_utf8(s.error))})
            return False

        return self.torrent_finished(torrent_handle, self.mod, self.result_queue)

    def torrent_finished(self, torrent_handle, mod, result_queue):
        # Save data that could come in handy in the future to a metadata file
        # Set resume data for quick checksum check
        resume_data = libtorrent.bencode(torrent_handle.write_resume_data())

        metadata_file = MetadataFile(os.path.join(mod.clientlocation, mod.foldername))
        metadata_file.read_data(ignore_open_errors=False)
        metadata_file.set_torrent_resume_data(resume_data)
        metadata_file.write_data()

        if self.force_termination:
            return False

        # Remove unused files
        assert(torrent_handle.has_metadata())  # Should have metadata if downloaded correctly
        torrent_info = torrent_handle.get_torrent_info()
        files_list = [entry.path.decode('utf-8') for entry in torrent_info.files()]
        cleanup_successful = check_mod_directories(files_list, mod.clientlocation, on_superfluous='remove')

        # Recreate the torrent file and store it in the metadata file for future checks
        recreated_torrent = libtorrent.create_torrent(torrent_info)
        bencoded_recreated_torrent = libtorrent.bencode(recreated_torrent.generate())
        metadata_file.set_torrent_content(bencoded_recreated_torrent)

        if not cleanup_successful:
            Logger.info("Could not perform mod {} cleanup. Marking torrent as dirty.".format(mod.foldername))
            metadata_file.set_dirty(True)
            metadata_file.write_data()

            self.result_queue.reject({'msg': 'Could not perform mod {} cleanup. Make sure the files are not in use by another program.'
                                             .format(mod.foldername)})
            return False
        else:
            metadata_file.set_dirty(False)
            metadata_file.write_data()

        return True


if __name__ == '__main__':
    class DummyMod:
        downloadurl = "http://archive.org/download/DebussyPrelduesBookI/DebussyPrelduesBookI_archive.torrent"
        # downloadurl = "file://test.torrent"
        clientlocation = ""
        foldername = "DebussyPrelduesBookI"
        version = "123"
        name = "name"

    class DummyQueue:
        def progress(self, d, frac):
            print 'Progress: {}'.format(unicode(d))

        def reject(self, d):
            print 'Reject: {}'.format(unicode(d))

    mod = DummyMod()
    queue = DummyQueue()

    ts = TorrentSyncer(queue, mod)
    # ts.init_libtorrent()
    # torrent_info = ts.get_torrent_info_from_file("test.torrent")

    # num_files = torrent_info.num_files()
    # print num_files

    # files_list = [entry.path.decode('utf-8') for entry in torrent_info.files()]
    # check_mod_directories(files_list)

    # print "File paths: ", file_paths
    # print "Dirs: ", dirs
    # print "Top dirs", top_dirs

    is_complete = torrent_utils.is_complete_quick(mod)
    print "Is complete:", is_complete

    if not is_complete:
        print "Syncing..."
        ts.sync()
