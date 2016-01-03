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

from sync.integrity import check_mod_directories, check_files_mtime_correct, is_complete_tfr_hack
from utils.metadatafile import MetadataFile
from time import sleep

class TorrentSyncer(object):
    _update_interval = 1
    _torrent_handle = None
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

    def decode_utf8(self, message):
        """Wrapper that prints the decoded message if an error occurs."""
        try:
            return message.decode('utf-8')
        except UnicodeDecodeError as ex:
            error_message = "{}. Text: {}".format(unicode(ex), repr(ex.args[1]))
            raise UnicodeError(error_message)

    def encode_utf8(self, message):
        """Wrapper that prints the encoded message if an error occurs."""
        try:
            return message.encode('utf-8')
        except UnicodeEncodeError as ex:
            error_message = "{}. Text: {}".format(unicode(ex), repr(ex.args[1]))
            raise UnicodeError(error_message)

    def init_libtorrent(self):
        """Perform the initialization of things that should be initialized once"""
        settings = libtorrent.session_settings()
        settings.user_agent = self.encode_utf8('TacBF (libtorrent/{})'.format(self.decode_utf8(libtorrent.version)))
        """When running on a network where the bandwidth is in such an abundance
        that it's virtually infinite, this algorithm is no longer necessary, and
        might even be harmful to throughput. It is adviced to experiment with the
        session_setting::mixed_mode_algorithm, setting it to session_settings::prefer_tcp.
        This setting entirely disables the balancing and unthrottles all connections."""
        settings.mixed_mode_algorithm = 0

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
            message = self.decode_utf8(alert.message())
            print "Alerts: Category: {}, Message: {}".format(alert.category(), message)
            torrent_log.append({'message': message, 'category': alert.category()})

        return torrent_log

    # TODO: Make this a static function
    def is_complete_quick(self):
        """Performs a quick check to see if the mod *seems* to be correctly installed.
        This check assumes no external changes have been made to the mods.

        1. Check if metadata file exists and can be opened (instant)
        2. Check if torrent is not dirty [download completed successfully] (instant)
        3. Check if torrent url matches (instant)
        4. Check if files have the right size and modification time (very quick)
        5. Check if there are no superfluous files in the directory (very quick)"""

        metadata_file = MetadataFile(os.path.join(self.mod.clientlocation, self.mod.foldername))

        # (1) Check if metadata can be opened
        try:
            metadata_file.read_data(ignore_open_errors=False)
        except IOError:
            print 'Metadata file could not be read successfully. Marking as not complete'
            return False

        # (2)
        if metadata_file.get_dirty():
            print 'Torrent marked as dirty (not completed successfully). Marking as not complete'
            return False

        # (3)
        if metadata_file.get_torrent_url() != self.mod.downloadurl:
            print 'Torrent urls differ. Marking as not complete'
            return False

        # Get data required for (4) and (5)
        torrent_content = metadata_file.get_torrent_content()
        if not torrent_content:
            print 'Could not get torrent file content. Marking as not complete'
            return False

        torrent_info = self.get_torrent_info_from_string(torrent_content)

        resume_data_bencoded = metadata_file.get_torrent_resume_data()
        if not resume_data_bencoded:
            print 'Could not get resume data. Marking as not complete'
            return False
        resume_data = libtorrent.bdecode(resume_data_bencoded)

        # (4)
        file_sizes = resume_data['file sizes']
        files = torrent_info.files()
        # file_path, size, mtime
        files_data = map(lambda x, y: (y.path.decode('utf-8'), x[0], x[1]), file_sizes, files)

        if not check_files_mtime_correct(self.mod.clientlocation, files_data):
            print 'Some files seem to have been modified in the meantime. Marking as not complete'
            return False

        # (5) Check if there are no additional files in the directory
        checksums = dict([(entry.path.decode('utf-8'), entry.filehash.to_bytes()) for entry in torrent_info.files()])
        files_list = checksums.keys()
        if not check_mod_directories(files_list, self.mod.clientlocation, on_superfluous='warn'):
            print 'Superfluous files in mod directory. Marking as not complete'
            return False

        return is_complete_tfr_hack(self.mod.name, files_list, checksums)
    """
    def create_flags(self):
        f = libtorrent.add_torrent_params_flags_t

        flags = 0
        flags |= f.flag_apply_ip_filter  # default
        flags |= f.flag_update_subscribe  # default
        #flags |= f.flag_merge_resume_trackers  # default off
        #flags |= f.flag_paused
        flags |= f.flag_auto_managed
        flags |= f.flag_override_resume_data
        #flags |= f.flag_seed_mode
        #flags |= f.flag_upload_mode
        #flags |= f.flag_share_mode
        flags |= f.flag_duplicate_is_error  # default?

        # no_recheck_incomplete_resume

        return flags
    """

    def handle_torrent_progress(self, s):
        """Just log the download progress for now."""
        download_fraction = s.progress
        download_kBps = s.download_rate / 1024
        upload_kBps = s.upload_rate / 1024
        state = self.decode_utf8(s.state.name)

        progress_message = '[{}] {}: {:0.2f}% ({:0.2f} KB/s)'.format(
                           self.mod.foldername, state, download_fraction * 100.0,
                           download_kBps)
        self.result_queue.progress({'msg': progress_message,
                                    'log': self.get_session_logs(),
                                   }, download_fraction)

        print '%.2f%% complete (down: %.1f kB/s up: %.1f kB/s peers: %d) %s' % \
              (s.progress * 100, download_kBps, upload_kBps, s.num_peers, state)

    def sync(self, force_sync=False):
        """
        Synchronize the mod directory contents to contain exactly the files that
        are described in the torrent file.

        force_sync - Assume no resume data is available. Manually recheck all the
                     checksums for all the files in the torrent description.
        """

        print "downloading ", self.mod.downloadurl, "to:", self.mod.clientlocation
        # TODO: Add the check: mod name == torrent directory name

        if not self.session:
            self.init_libtorrent()


        # === Metadata handling ===
        metadata_file = MetadataFile(os.path.join(self.mod.clientlocation, self.mod.foldername))
        metadata_file.read_data(ignore_open_errors=True)  # In case the mod does not exist, we would get an error

        metadata_file.set_dirty(True)  # Set as dirty in case this process is not terminated cleanly

        # If the torrent url changed, invalidate the resume data
        old_torrent_url = metadata_file.get_torrent_url()
        if old_torrent_url != self.mod.downloadurl or force_sync:
            metadata_file.set_torrent_resume_data("")
            metadata_file.set_torrent_url(self.mod.downloadurl)

        metadata_file.write_data()
        # End of metadata handling


        # === Torrent parameters ===
        params = {
            'save_path': self.encode_utf8(self.mod.clientlocation),
            'storage_mode': libtorrent.storage_mode_t.storage_mode_allocate,  # Reduce fragmentation on disk
            # 'flags': self.create_flags()
        }

        # Configure torrent source
        if self.mod.downloadurl.startswith('file://'):  # Local torrent from file
            torrent_info = self.get_torrent_info_from_file(self.mod.downloadurl[len('file://'):])
            params['ti'] = torrent_info
        else:  # Torrent from url
            params['url'] = self.encode_utf8(self.mod.downloadurl)

        # Add optional resume data
        resume_data = metadata_file.get_torrent_resume_data()
        if resume_data:  # Quick resume torrent from data saved last time the torrent was run
            params['resume_data'] = resume_data

        # Launch the download of the torrent
        torrent_handle = self.session.add_torrent(params)
        self._torrent_handle = torrent_handle

        # === Main loop ===
        # Loop while the torrent is not completely downloaded
        s = torrent_handle.status()
        while (not torrent_handle.is_seed() and not s.error):
            self.handle_torrent_progress(s)

            # TODO: Save resume_data periodically
            sleep(self._update_interval)
            s = torrent_handle.status()

        self.handle_torrent_progress(s)

        if s.error:
            self.result_queue.reject({'msg': 'An error occured: Libtorrent error: {}'.format(self.decode_utf8(s.error))})
            return False

        # Save data that could come in handy in the future to a metadata file
        # Set resume data for quick checksum check
        resume_data = libtorrent.bencode(torrent_handle.write_resume_data())
        metadata_file.set_torrent_resume_data(resume_data)
        metadata_file.write_data()

        # Remove unused files
        assert(self._torrent_handle.has_metadata())  # Should have metadata if downloaded correctly
        torrent_info = self._torrent_handle.get_torrent_info()
        files_list = [entry.path.decode('utf-8') for entry in torrent_info.files()]
        cleanup_successful = check_mod_directories(files_list, self.mod.clientlocation, on_superfluous='remove')

        # Recreate the torrent file and store it in the metadata file for future checks
        recreated_torrent = libtorrent.create_torrent(torrent_info)
        bencoded_recreated_torrent = libtorrent.bencode(recreated_torrent.generate())
        metadata_file.set_torrent_content(bencoded_recreated_torrent)

        if not cleanup_successful:
            print "Could not perform mod {} cleanup. Marking torrent as dirty.".format(self.mod.foldername)
            metadata_file.set_dirty(True)
            metadata_file.write_data()

            self.result_queue.reject({'msg': 'Could not perform mod {} cleanup. Make sure the files are not in use by another program.'
                                             .format(self.mod.foldername)})
            return False
        else:
            metadata_file.set_version(self.mod.version)
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

    is_complete = ts.is_complete_quick()
    print "Is complete:", is_complete

    if not is_complete:
        print "Syncing..."
        ts.sync()
