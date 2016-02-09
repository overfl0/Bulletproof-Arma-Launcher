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

    def __init__(self, result_queue, mods):
        """
        constructor

        Args:
            result_queue: the queue object where you can push the dict in
            mods: a mod list that will be synced (or seeded) by sync()
        """
        super(TorrentSyncer, self).__init__()

        self.result_queue = result_queue
        self.mods = mods
        self.force_termination = False

        for m in mods:
            m.finished_hook_ran = False
            m.can_save_resume_data = False

        self.init_libtorrent()

    def init_libtorrent(self):
        """Perform the initialization of things that should be initialized once"""
        if self.session:
            return

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

    def log_torrent_progress(self, s, mod_name):
        """Just log the download progress for now."""
        # download_fraction = s.progress
        download_kBps = s.download_rate / 1024
        upload_kBps = s.upload_rate / 1024
        state = decode_utf8(s.state.name)

#         progress_message = '[{}] {}: {:0.2f}% ({:0.2f} KB/s)'.format(
#                            mod_name, state, download_fraction * 100.0,
#                            download_kBps)
#         self.result_queue.progress({'msg': progress_message,
#                                     'log': self.get_session_logs(),
#                                     }, download_fraction)

        Logger.info('Progress: [{}] {:.2f}% complete (down: {:.1f} kB/s up: {:.1f} kB/s peers: {}) {}'.format(
                    mod_name, s.progress * 100, download_kBps, upload_kBps, s.num_peers, state))

    def mods_with_valid_handle(self):
        """Return a list of mods with a valid handle."""
        for mod in self.mods:
            if mod.torrent_handle.is_valid():
                yield mod

    def log_session_progress(self):
        """Log the progress of syncing the torrents.
        Progress for each individual torrent is written to the log file.
        Progress for the whole session is shown in the status label.

        - If at least one torrent is downloading its metadata, the progress will
        be "Downloading metadata..."
        - If at least one torrent is checking its pieces, the progress will be
        "Checking missing pieces..."
        """

        session_logs = self.get_session_logs()

        # If not all torrents have retrieved metadata, just show a message
        if not all(mod.torrent_handle.has_metadata() for mod in self.mods_with_valid_handle()):
            self.result_queue.progress({'msg': 'Downloading metadata...',
                                        'log': session_logs,
                                        }, 0)
            return

        # We can now assume that every torrent has got the metadata downloaded
        # so we can get its size on disk

        status = self.session.status()

        total_size = 0.0
        downloaded_size = 0.0
        unfinished_mods = []

        for mod in self.mods_with_valid_handle():
            downloaded_size += mod.status.total_wanted_done
            total_size += mod.status.total_wanted

            if mod.status.total_wanted_done != mod.status.total_wanted:
                unfinished_mods.append(mod.foldername)

        if total_size == 0:
            total_size = 1
        download_fraction = downloaded_size / total_size

        action = 'Syncing:'
        # If at least one torrent is checking its pieces, show a message
        for mod in self.mods_with_valid_handle():
            if mod.status.state == libtorrent.torrent_status.checking_files:
                action = 'Checking missing pieces:'
                break

        progress_message = '{} {:0.2f}% complete. ({:0.2f} KB/s)\n{}'.format(
                           action,
                           download_fraction * 100.0,
                           status.payload_download_rate / 1024,
                           ' | '.join(unfinished_mods))

        self.result_queue.progress({'msg': progress_message,
                                    'log': self.get_session_logs(),
                                    }, download_fraction)
        Logger.info('Progress: {}'.format(progress_message))

    def start_syncing(self, mod, force_sync=False):
        """Create a torrent handle for a mod to be downloaded.
        This effectively starts the download.
        """
        Logger.info('Sync: Downloading {} to {}'.format(mod.downloadurl, mod.clientlocation))
        # TODO: Add the check: mod name == torrent directory name

        # === Metadata handling ===
        metadata_file = MetadataFile(os.path.join(mod.clientlocation, mod.foldername))
        metadata_file.read_data(ignore_open_errors=True)  # In case the mod does not exist, we would get an error

        metadata_file.set_dirty(True)  # Set as dirty in case this process is not terminated cleanly

        # If the torrent url changed, invalidate the resume data
        old_torrent_url = metadata_file.get_torrent_url()
        if old_torrent_url != mod.downloadurl or force_sync:
            metadata_file.set_torrent_resume_data("")
            # print "Setting torrent url to {}".format(mod.downloadurl)
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

    def get_torrents_status(self):
        """Get the status of all torrents with valid handles and cache them in
        the TorrentSyncer class.
        This allows us to access this data later without any performance penalty.
        """
        for mod in self.mods:
            if mod.torrent_handle.is_valid():
                mod.status = mod.torrent_handle.status()

    def all_torrents_ran_finished_hooks(self):
        """Check if all torrents have been downloaded, their files have been
        synchronized to the disk and their post-download hooks have been run.
        """
        return all(mod.finished_hook_ran for mod in self.mods)

    def pause_all_torrents(self):
        """Pause all torrents with valid handles."""
        for mod in self.mods:
            if not mod.torrent_handle.is_valid():
                continue

            mod.torrent_handle.auto_managed(False)
            mod.torrent_handle.pause()

    def pause_torrent(self, mod):
        """Pause a torrent paired with a mod."""
        if mod.torrent_handle.is_valid():
            mod.torrent_handle.auto_managed(False)
            mod.torrent_handle.pause()

    def resume_torrent(self, mod):
        """Resume a torrent paired with a mod."""
        if mod.torrent_handle.is_valid():
            mod.torrent_handle.auto_managed(True)
            mod.torrent_handle.resume()

    def syncing_finished(self):
        """Check whether all torrents are in a state where every torrens has been synced.
        If this is the case, we can then stop downloading or seeding at any time.
        """
        for mod in self.mods:
            # print "Checking mod {}".format(mod.foldername)
            # import IPython; IPython.embed()
            # If a handle is not valid (torrent error) we skip it.
            # This contributes to finished torrents.
            if not mod.torrent_handle.is_valid():
                continue

            # Skip torrents that are in an error state
            if mod.status.error:
                continue

            # Wait until the hooks are ran if we're not terminating forcefully
            if not mod.finished_hook_ran and not self.force_termination:
                # print "mod {} not mod.finished_hook_ran".format(mod.foldername)
                return False

            if not mod.torrent_handle.is_paused():
                # print "mod {} not paused".format(mod.foldername)
                return False

        return True

    def sync(self, force_sync=False):
        """
        Synchronize the mod directory contents to contain exactly the files that
        are described in the torrent file.

        force_sync - Assume no resume data is available. Manually recheck all the
                     checksums for all the files in the torrent description.

        Individual torrent states:
        1) Downloading    -> Wait until it starts seeding
        2) Seeding        -> Pause the torrent to sync it to disk
        3) Paused         -> Data has been synced, We can start seeding while
                             waiting for the other torrents to download.
        4) Waiting seed   -> When all torrents are waiting seeds, pause to stop
        5) Paused to stop -> When all torrents are paused to stop, stop syncing
        """

        sync_success = True

        for mod in self.mods:
            torrent_handle = self.start_syncing(mod, force_sync)
            mod.torrent_handle = torrent_handle

        self.get_torrents_status()

        # Loop until state (5). All torrents finished and paused
        while not self.syncing_finished():
            # We are canceling the downloads
            if self.result_queue.wants_termination():
                Logger.info('TorrentSyncer wants termination')
                self.force_termination = True

            self.log_session_progress()

            for mod in self.mods:
                if not mod.torrent_handle.is_valid():
                    Logger.info('Sync: Torrent {} - torrent handle is invalid. Terminating'.format(mod.foldername))
                    self.force_termination = True
                    continue

                # It is assumed that all torrents below have a valid torrent_handle
                self.log_torrent_progress(mod.status, mod.foldername)

                if mod.status.error:
                    Logger.info('Sync: Torrent {} in error state. Terminating. Error string: {}'.format(mod.foldername, decode_utf8(mod.status.error)))
                    self.force_termination = True
                    continue  # Torrent is now paused

                # Allow saving fast-resume data only after finishing checking the files of the torrent
                # If we save the data from a torrent while being checked, this will result
                # in marking the torrent as having only a fraction of data it really has.
                if mod.status.state in (libtorrent.torrent_status.downloading,
                                        libtorrent.torrent_status.finished,
                                        libtorrent.torrent_status.seeding):
                    mod.can_save_resume_data = True

                # Shut the torrent if we are terminating
                if self.force_termination:
                    if not mod.torrent_handle.is_paused():  # Don't spam logs
                        Logger.info('Sync: Pausing torrent {} for termination'.format(mod.foldername))
                    self.pause_torrent(mod)

                # If state (2). Request pausing the torrent to synchronize data to disk
                if not mod.finished_hook_ran and mod.torrent_handle.is_seed():
                    if not mod.torrent_handle.is_paused():
                        Logger.info('Sync: Pausing torrent {} for disk syncing'.format(mod.foldername))
                    self.pause_torrent(mod)

                # If state (3). Run the hooks and maybe start waiting-seed
                if not mod.finished_hook_ran and mod.torrent_handle.is_seed() and mod.torrent_handle.is_paused():
                    Logger.info('Sync: Torrent {} paused. Running finished_hook'.format(mod.foldername))

                    hook_successful = self.torrent_finished_hook(mod)
                    if not hook_successful:
                        self.result_queue.reject({'msg': 'Could not perform mod {} cleanup. Make sure the files are not in use by another program.'
                                                  .format(mod.foldername)})
                        Logger.info('Sync: Could not perform mod {} cleanup. Make sure the files are not in use by another program.'
                                    .format(mod.foldername))
                        sync_success = False
                        self.force_termination = True

                    mod.finished_hook_ran = True

                    # Do not go into state (4) if we are terminating or it's the
                    # only torrent being synced
                    if not self.force_termination and len(self.mods) != 1:
                        Logger.info('Sync: Seeding {} again until all downloads are done.'.format(mod.foldername))
                        self.resume_torrent(mod)

            # If all are in state (4)
            if self.all_torrents_ran_finished_hooks():
                Logger.info('Sync: Pausing all torrents for syncing end.')
                self.pause_all_torrents()

            sleep(self._update_interval)
            self.get_torrents_status()

        Logger.info('Sync: Main loop exited')

        for mod in self.mods:
            if not mod.torrent_handle.is_valid():
                self.result_queue.reject({'details': 'Mod {} torrent handle is invalid'.format(mod.foldername)})
                sync_success = False
                continue

            self.save_resume_data(mod)

            self.log_torrent_progress(mod.status, mod.foldername)
            if mod.status.error:
                self.result_queue.reject({'details': 'An error occured: Libtorrent error: {}'.format(decode_utf8(mod.status.error))})
                sync_success = False

        return sync_success

    def save_resume_data(self, mod):
        """Save the resume data of the mod that will allow a faster restart in the future."""
        if not mod.torrent_handle.is_valid():
            return

        if not mod.torrent_handle.has_metadata():
            return

        if not mod.can_save_resume_data:
            return

        Logger.info('Sync: saving fast-resume metadata for mod {}'.format(mod.foldername))

        # Save data that could come in handy in the future to a metadata file
        # Set resume data for quick checksum check
        resume_data = libtorrent.bencode(mod.torrent_handle.write_resume_data())
        metadata_file = MetadataFile(os.path.join(mod.clientlocation, mod.foldername))
        metadata_file.read_data(ignore_open_errors=False)
        metadata_file.set_torrent_resume_data(resume_data)
        metadata_file.write_data()

    def torrent_finished_hook(self, mod):
        """Hook that is called when a torrent has been successfully and fully downloaded.
        This hook then removes any superfluous files in the directory and updates
        the metadata file.

        Return whether then mod has been synced successfully and no superfluous
        files are present in the directory.
        """
        if not mod.torrent_handle.has_metadata():
            Logger.error('Finished_hook: torrent {} has no metadata!'.format(mod.foldername))
            return False

        metadata_file = MetadataFile(os.path.join(mod.clientlocation, mod.foldername))
        metadata_file.read_data(ignore_open_errors=False)

        # Remove unused files
        torrent_info = mod.torrent_handle.get_torrent_info()
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

            return False
        else:
            metadata_file.set_dirty(False)
            metadata_file.write_data()

        return True


if __name__ == '__main__':
    Logger.setLevel(level='INFO')

    class DummyMod:
        def __init__(self, downloadurl, clientlocation, foldername, name):
            self.downloadurl = downloadurl
            self.clientlocation = clientlocation
            self.foldername = foldername
            self.name = name

    class DummyQueue:
        def progress(self, d, frac):
            Logger.info('Progress: {}'.format(unicode(d)))

        def reject(self, d):
            Logger.error('Reject: {}'.format(unicode(d)))

        def wants_termination(self):
            return False

    def mod_helper(url):
        import re
        foldername = re.search('(@.*?)-', url).group(1)

        return DummyMod(downloadurl=url,
                        clientlocation='',
                        foldername=foldername,
                        name=foldername.replace('@', ''))

    mod1 = mod_helper('http://launcher.tacbf.com/tacbf/updater/torrents/@CBA_A3-2015-12-01_1449001363.torrent')
    mod2 = mod_helper('http://launcher.tacbf.com/tacbf/updater/torrents/@TacBF-2015-12-31_1451563576.torrent')
    mod3 = mod_helper('http://launcher.tacbf.com/tacbf/updater/torrents/@task_force_radio-2015-10-12_1444682049.torrent')
    mods = [mod1, mod2, mod3]
    # mod = mod_helper('')
    queue = DummyQueue()

    ts = TorrentSyncer(queue, mods)

    completed = []
    for mod in mods:
        is_complete = torrent_utils.is_complete_quick(mod)
        print '{} is complete:'.format(mod.foldername), is_complete
        completed.append(is_complete)

    if not all(completed):
        print 'Syncing...'
        ts.sync()
