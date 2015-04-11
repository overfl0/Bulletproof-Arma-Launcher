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
        """Perform the initialization of things that should be initialized once"""
        settings = libtorrent.session_settings()
        settings.user_agent = 'TacBF (libtorrent/{})'.format(libtorrent.version)

        self.session = libtorrent.session()
        self.session.listen_on(6881, 6891)  # This is just a port suggestion. On failure, the port is automatically selected.

        # TODO: self.session.set_download_rate_limit(down_rate)
        # TODO: self.session.set_upload_rate_limit(up_rate)

        self.session.set_settings(settings)

    def init_torrent_data_from_string(self, bencoded):
        """Initialize torrent metadata from a bencoded string."""

        self.torrent_metadata = libtorrent.bdecode(bencoded)
        self.torrent_info = libtorrent.torrent_info(self.torrent_metadata)

    def init_torrent_data_from_file(self, filename):
        """Initialize torrent metadata from a file."""
        with open(filename, 'rb') as file_handle:
            file_contents = file_handle.read()

            self.init_torrent_data_from_string(file_contents)

    def parse_torrent_inodes(self):
        """Computes the file paths, directories and top directories contained in a torrent."""

        self.file_paths = set()
        self.dirs = set()
        self.top_dirs = set()

        for torrent_file in self.torrent_info.files():
            self.file_paths.add(torrent_file.path)
            dir_path = os.path.dirname(torrent_file.path)

            while dir_path:  # Go up the directory structure until the end
                if dir_path in self.dirs:  # If already processed for another file
                    break

                self.dirs.add(dir_path)
                parent_dir = os.path.dirname(dir_path)
                if not parent_dir:
                    self.top_dirs.add(dir_path)

                dir_path = parent_dir

    def cleanup_mod_directories(self):
        """Remove files or directories that do not belong to the torrent file
        and were probably removed in an update.
        To prevent accidental file removal, this function will only remove files
        that are at least one directory deep in the file structure!
        As all multi-file torrents *require* one root directory that holds those
        files, this should not be an issue.
        This function will skip files or directories that match file_whitelist.

        Returns if the directory has been cleaned sucessfully. Do not ignore this value!
        If unsuccessful at removing files, the mod should NOT be considered ready to play."""

        # TODO: Handle unicode file names
        def raiser(exception):  # I'm sure there must be some builtin to do this :-/
            raise exception

        whitelist = ('.tbfmetadata',)
        base_directory = ""  # TODO: Fill me
        base_directory = os.path.realpath(base_directory)
        success = True

        try:
            for directory in self.top_dirs:
                if directory in whitelist:
                    continue

                full_base_path = os.path.join(base_directory, directory)
                for (dirpath, dirnames, filenames) in os.walk(full_base_path, topdown=True, onerror=raiser, followlinks=False):
                    relative_path = os.path.relpath(dirpath, base_directory)
                    print 'In directory: {}'.format(relative_path)

                    # First check files in this directory
                    for file_name in filenames:
                        if file_name in whitelist:
                            print 'File {} in whitelist, skipping...'.format(file_name)
                            continue

                        relative_file_name = os.path.join(relative_path, file_name)
                        print 'Checking file: {}'.format(relative_file_name)
                        if relative_file_name in self.file_paths:
                            continue  # File present in the torrent, nothing to see here

                        full_file_path = os.path.join(dirpath, file_name)
                        print 'Removing file: {}'.format(full_file_path)
                        #os.unlink(full_file_path)

                    # Now check directories
                    # Remove directories that match whitelist from checking and descending into them
                    dirnames[:] = [d for d in dirnames if d not in whitelist]
                    # Iterate over a copy because we'll be deleting items from the original
                    for dir_name in dirnames[:]:
                        relative_dir_path = os.path.join(relative_path, dir_name)
                        print 'Checking dir: {}'.format(relative_dir_path)

                        if relative_dir_path in self.dirs:
                            continue  # Directory present in the torrent, nothing to see here

                        full_directory_path = os.path.join(dirpath, dir_name)
                        print 'Removing directory: {}'.format(full_directory_path)
                        dirnames.remove(dir_name)

                        #shutil.rmtree(full_directory_path)

        except (OSError, WindowsError) as exception:
            success = False

        return success

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

        metadata_file = MetadataFile(os.path.join(self.mod.clientlocation, self.mod.name))
        metadata_file.read_data(ignore_open_errors=True)  # In case the mod does not exist, we would get an error

        metadata_file.set_dirty(True)  # Set as dirty in case this process is not terminated cleanly
        metadata_file.write_data()

        if not self.session:
            self.init_libtorrent()

        self.init_torrent_data_from_file(self.mod.downloadurl)

        params = {
            'save_path': self.mod.clientlocation,
            'storage_mode': libtorrent.storage_mode_t.storage_mode_allocate,  # Reduce fragmentation on disk
            'ti': self.torrent_info
            # 'url': http://....torrent
        }
        resume_data = metadata_file.get_torrent_resume_data()
        if resume_data:  # Quick resume torrent from data saved last time the torrent was run
            params['resume_data'] = resume_data

        torrent_handle = self.session.add_torrent(params)
        self._torrent_handle = torrent_handle

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
        downloadurl = "test.torrent"
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
    ts.init_torrent_data_from_file("test.torrent")

    #num_files = ts.torrent_info.num_files()
    ts.parse_torrent_inodes()
    print "asd"
    ts.cleanup_mod_directories()
    print "ert"

    #print "File paths: ", ts.file_paths
    #print "Dirs: ", ts.dirs
    #print "Top dirs", ts.top_dirs

    #ts.sync()
