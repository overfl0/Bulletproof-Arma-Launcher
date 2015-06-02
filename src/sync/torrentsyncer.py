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
import shutil

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

    def grab_torrent_file_structure(self, torrent_info):
        """Computes the file paths, directories and top directories contained in a torrent."""

        self.file_paths = set()
        self.dirs = set()
        self.top_dirs = set()

        for torrent_file in torrent_info.files():
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

    def _unlink_safety_assert(self, base_path, file_path, action="remove"):
        """Asserts that the file_path string starts with base_path string.
        If this is not true then raise an exception"""

        real_base_path = os.path.realpath(base_path)
        real_file_path = os.path.realpath(file_path)
        if not real_file_path.startswith(real_base_path):
            message = "Something fishy is happening. Attempted to {} {} which is not inside {}!".format(
                action, real_file_path, real_base_path)
            raise Exception(message)

    def _safer_unlink(self, base_path, file_path):
        """Checks if the base_path contains the file_path and removes file_path if true"""

        self._unlink_safety_assert(base_path, file_path)
        os.unlink(file_path)

    def _safer_rmtree(self, base_path, directory_path):
        """Checks if the base_path contains the directory_path and removes directory_path if true"""

        self._unlink_safety_assert(base_path, directory_path)
        shutil.rmtree(directory_path)

    def check_mod_directories(self, base_directory, action='warn'):
        """Check if all files and directories present in the mod directories belong
        to the torrent file. If not, remove those if action=='remove' or return False
        if action=='warn'.

        base_directory is the directory to which mods are downloaded.
        For example: if the mod directory is C:\Arma\@MyMod, base_directory should be C:\Arma.

        action is the action to perform when superfluous files are found:
            'warn': return False
            'remove': remove the file or directory

        To prevent accidental file removal, this function will only remove files
        that are at least one directory deep in the file structure!
        As all multi-file torrents *require* one root directory that holds those
        files, this should not be an issue.
        This function will skip files or directories that match the 'whitelist' variable.

        Returns if the directory has been cleaned sucessfully or if all files present
        are supposed to be there. Do not ignore this value!
        If unsuccessful at removing files, the mod should NOT be considered ready to play."""

        # TODO: Handle unicode file names
        def raiser(exception):  # I'm sure there must be some builtin to do this :-/
            raise exception

        if not action in ('warn', 'remove'):
            raise Exception('Unknown action: {}'.format(action))

        # Whitelist our and PWS metadata files
        whitelist = (MetadataFile.file_name, '.synqinfo')
        base_directory = os.path.realpath(base_directory)
        print "Cleaning up base_directory:", base_directory
        success = True

        try:
            for directory in self.top_dirs:
                if directory in whitelist:
                    continue

                full_base_path = os.path.join(base_directory, directory)
                self._unlink_safety_assert(base_directory, full_base_path, action='enter')
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

                        if action == 'remove':
                            print 'Removing file: {}'.format(full_file_path)
                            self._safer_unlink(full_base_path, full_file_path)

                        elif action == 'warn':
                            print 'Superfluous file: {}'.format(full_file_path)
                            return False

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

                        if action == 'remove':
                            print 'Removing directory: {}'.format(full_directory_path)
                            dirnames.remove(dir_name)

                            self._safer_rmtree(full_base_path, full_directory_path)

                        elif action == 'warn':
                            print 'Superfluous directory: {}'.format(full_directory_path)
                            return False

        except OSError as exception:
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

    def check_files_mtime_correct(self, torrent_info, resume_data):
        """Checks if all files have the right size and modification time.
        If the size or modification time differs, the file is considered modified
        and thus the check fails.

        Attention: The modification time check accuracy depends on a number of
        things such as the underlying File System type. Files are also allowed to be
        up to 5 minutes more recent than stated as per libtorrent implementation."""

        file_sizes = resume_data['file sizes']
        files = torrent_info.files()

        # file_path, size, mtime
        files_data = map(lambda x, y: (y.path, x[0], x[1]), file_sizes, files)

        for file_path, size, mtime in files_data:
            try:
                full_file_path = os.path.join(self.mod.clientlocation, file_path)
                file_stat = os.stat(full_file_path)
            except OSError:
                print 'Could not perform stat on', full_file_path
                return False

            # print file_path, file_stat.st_mtime, mtime
            # Values for st_size and st_mtime based on libtorrent/src/storage.cpp: 135-190 // match_filesizes()
            if file_stat.st_size < size:  # Actually, not sure why < instead of != but kept this to be compatible with libtorrent
                print 'Incorrect file size for', full_file_path
                return False

            # Allow for 1 sec discrepancy due to FAT32
            # Also allow files to be up to 5 minutes more recent than stated
            if int(file_stat.st_mtime) > mtime + 5 * 60 or int(file_stat.st_mtime) < mtime - 1:
                print 'Incorrect modification time for', full_file_path
                return False

        return True

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
        if not self.check_files_mtime_correct(torrent_info, resume_data):
            print 'Some files seem to have been modified in the meantime. Marking as not complete'
            return False

        # (5) Check if there are no additional files in the directory
        self.grab_torrent_file_structure(torrent_info)
        if not self.check_mod_directories(self.mod.clientlocation, action='warn'):
            print 'Superfluous files in mod directory. Marking as not complete'
            return False

        return True
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

    def sync(self, force_sync=False):
        """
        Synchronize the mod directory contents to contain exactly the files that
        are described in the torrent file.

        force_sync - Assume no resume data is available. Manually recheck all the
                     checksums for all the files in the torrent description.
        """

        print "downloading ", self.mod.downloadurl, "to:", self.mod.clientlocation
        #TODO: Add the check: mod name == torrent directory name

        if not self.session:
            self.init_libtorrent()


        ### Metadata handling
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


        ### Torrent parameters
        params = {
            'save_path': self.mod.clientlocation,
            'storage_mode': libtorrent.storage_mode_t.storage_mode_allocate,  # Reduce fragmentation on disk
            #'flags': self.create_flags()
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
        s = torrent_handle.status()
        while (not torrent_handle.is_seed() and not s.error):

            download_fraction = s.progress
            download_kbs = s.download_rate / 1024

            self.result_queue.progress({'msg': '[%s] %s: %.2f%%' % (self.mod.foldername, str(s.state), download_fraction * 100.0),
                                        'log': self.get_session_logs(),
                                       }, download_fraction)

            print '%.2f%% complete (down: %.1f kB/s up: %.1f kB/s peers: %d) %s' % \
                  (s.progress * 100, s.download_rate / 1024, s.upload_rate / 1024, s.num_peers, s.state)

            # TODO: Save resume_data periodically
            sleep(self._update_interval)
            s = torrent_handle.status()

        if s.error:
            self.result_queue.reject({'msg': 'An error occured: {}'.format(s.error)})
            return

        #print torrent_handle.get_torrent_info()
        # Download finished. Performing housekeeping
        download_fraction = 1.0
        self.result_queue.progress({'msg': '[%s] %s' % (self.mod.foldername, torrent_handle.status().state),
                                    'log': self.get_session_logs(),
                                   }, download_fraction)


        # Save data that could come in handy in the future to a metadata file
        # Set resume data for quick checksum check
        resume_data = libtorrent.bencode(torrent_handle.write_resume_data())
        metadata_file.set_torrent_resume_data(resume_data)
        metadata_file.write_data()

        # Remove unused files
        assert(self._torrent_handle.has_metadata())  # Should have metadata if downloaded correctly
        torrent_info = self._torrent_handle.get_torrent_info()
        self.grab_torrent_file_structure(torrent_info)
        cleanup_successful = self.check_mod_directories(self.mod.clientlocation, action='remove')

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
        else:
            metadata_file.set_version(self.mod.version)
            metadata_file.set_dirty(False)
            metadata_file.write_data()


if __name__ == '__main__':
    class DummyMod:
        downloadurl = "https://archive.org/download/DebussyPrelduesBookI/DebussyPrelduesBookI_archive.torrent"
        #downloadurl = "file://test.torrent"
        clientlocation = ""
        name = "DebussyPrelduesBookI"
        version = "123"

    class DummyQueue:
        def progress(self, d, frac):
            print 'Progress: {}'.format(str(d))

        def reject(self, d):
            print 'Reject: {}'.format(str(d))

    mod = DummyMod()
    queue = DummyQueue()

    ts = TorrentSyncer(queue, mod)
    #ts.init_libtorrent()
    #torrent_info = ts.get_torrent_info_from_file("test.torrent")

    #num_files = torrent_info.num_files()
    #print num_files

    #ts.grab_torrent_file_structure(torrent_info)
    #ts.check_mod_directories()

    #print "File paths: ", ts.file_paths
    #print "Dirs: ", ts.dirs
    #print "Top dirs", ts.top_dirs

    is_complete = ts.is_complete_quick()
    print "Is complete:", is_complete

    if not is_complete:
        print "Syncing..."
        ts.sync()
