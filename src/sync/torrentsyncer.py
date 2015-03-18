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
        self.session = libtorrent.session()
        self.session.listen_on(6881, 6891)  # TODO: check if this is necessary (maybe rely on automatic port selection?)

    def init_metadata_from_string(self, bencoded):
        """Initialize torrent metadata from a bencoded string."""

        self.torrent_metadata = libtorrent.bdecode(bencoded)
        self.torrent_info = libtorrent.torrent_info(self.torrent_metadata)

    def init_metadata_from_file(self, filename):
        """Initialize torrent metadata from a file."""
        with open(filename, 'rb') as file_handle:
            file_contents = file_handle.read()

            self.init_metadata_from_string(file_contents)

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
        This will skip files or directories that match file_whitelist.

        Returns if the directory has been cleaned sucessfully. Do not ignore this value!
        If unsuccessful at removing files, the mod should NOT be considered ready to play."""

        #TODO: Handle unicode file names
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

    def sync(self):
        """
        helper function to download. It needs to be
        on module level since multiprocessing needs
        pickable objects
        """
        """Attention!
        This is just a proof of concept module for now.
        No extensive checks are performed! This module is the definition of wishful thinking.
        """

        print "downloading ", self.mod.downloadurl, "to:", self.mod.clientlocation
        print "TODO: Download this to a temporary location and copy/move afterwards"

        if not self.session:
            self.init_libtorrent()

        self.init_metadata_from_file(self.mod.downloadurl)

        params = {
            'save_path': self.mod.clientlocation,
            'storage_mode': libtorrent.storage_mode_t.storage_mode_sparse,
            'ti': self.torrent_info
        }
        torrent_handle = self.session.add_torrent(params)

        while (not torrent_handle.is_seed()):
            s = torrent_handle.status()

            download_fraction = s.progress
            download_kbs = s.download_rate / 1024

            state_str = ['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating']
            print '%.2f%% complete (down: %.1f kB/s up: %.1f kB/s peers: %d) %s' % \
                (s.progress * 100, s.download_rate / 1024, s.upload_rate / 1024, \
                s.num_peers, s.state)

            self.result_queue.put({
                'progress': download_fraction,
                'kbpersec': download_kbs,
                'status': str(s.state)})
            sleep(self._update_interval)

        self.result_queue.put({
            'progress': 1.0,
            'kbpersec': 0,
            'status': 'finished'})

if __name__ == '__main__':
    class DummyMod:
        downloadurl = "test.torrent"
        clientlocation = ""
    class DummyQueue:
        def put(self, d):
            print str(d)

    mod = DummyMod()
    queue = DummyQueue()

    ts = TorrentSyncer(queue, mod)
    ts.init_metadata_from_file("test.torrent")

    #num_files = ts.torrent_info.num_files()
    ts.parse_torrent_inodes()
    ts.cleanup_mod_directories()

    #print "File paths: ", ts.file_paths
    #print "Dirs: ", ts.dirs
    #print "Top dirs", ts.top_dirs

    #ts.sync()
