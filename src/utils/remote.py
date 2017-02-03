# Bulletproof Arma Launcher
# Copyright (C) 2017 Lukasz Taczuk
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

if __name__ == '__main__':
    import site
    import os
    file_directory = os.path.dirname(os.path.realpath(__file__))
    site.addsitedir(os.path.abspath(os.path.join(file_directory, '..')))


import os
import paramiko
import posixpath
import random
import socket

from kivy.logger import Logger
from paramiko.sftp import CMD_EXTENDED
from utils.context import ignore_nosuchfile_ioerror


# The remote is using a posix style paths ('/')
join = posixpath.join


class RemoteMissingKeyPolicy(paramiko.client.MissingHostKeyPolicy):
    def __init__(self, *args, **kwargs):
        super(RemoteMissingKeyPolicy, self).__init__(*args, **kwargs)

    def missing_host_key(self, client, hostname, key):
        """This method is called each time a connection is made to a server that
        does not have a known key to the launcher.
        To reject the key, raise an exception.
        To accept the key, return.
        """

        Logger.info('RemoteConection: Missing key: {} {}'.format(
            hostname, key.get_fingerprint().encode('hex')))
        Logger.info('RemoteConection: Accepting it.')

        return


class RemoteConection(object):
    """The class that allows talking to an SFTP server and execute commands
    remotely. Maybe it can be replaced by a more generic class with more
    backends supported in the future.
    """

    def __init__(self, host=None, username=None, password=None, port=22, *args, **kwargs):
        """Connect to the server using the given credentials.
        Can be used in a python with statement.

        with RemoteConection(...) as connection:
            connection.do_stuff()
        """

        super(RemoteConection, self).__init__(*args, **kwargs)

        self.host = host
        self.username = username
        self.password = password
        self.port = port

        self.client = None
        self.sftp = None

        self.connect()

    def __enter__(self):
        return self

    def __exit__(self, type_, value, traceback):
        self.close()

    def _random_str(self, length=10):
        """Return a string of a given length. Useful for temporary files.
        Those files of course DO NOT give a guarantee of uniqueness.
        """

        return ''.join(str(int(random.random() * 10)) for _ in range(length))

    def close(self):
        """Close the connection. YOU ALWAYS HAVE TO CALL IT!
        Failure to do so may lead to process hanging on exit, according to
        Paramiko documentation.
        The only case when you don't have to call close() is when you're using
        a python with statement.
        """

        if self.client is not None:
            Logger.info('RemoteConection.close: Closing the connection.')

            self.client.close()
            self.client = None
            self.sftp = None

    def connect(self):
        """Perform the connection.
        Uses values passed in the constructor.
        """

        self.close()

        try:
            client = paramiko.client.SSHClient()
            client.load_system_host_keys()
            # client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.set_missing_host_key_policy(RemoteMissingKeyPolicy())
            # TODO: store the server key somewhere after the first connection!
            # and don't use AutoAddPolicy

            try:
                Logger.info('RemoteConection.connect: Connecting to {}@{}...'.format(
                    self.username, self.host))
                client.connect(self.host,
                               username=self.username,
                               password=self.password,
                               port=self.port,
                               timeout=5)

            except paramiko.BadHostKeyException:
                raise

            except paramiko.AuthenticationException:
                raise

            except paramiko.SSHException:
                raise

            except socket.error as ex:
                if ex.errno == 10060:
                    Logger.error('RemoteConection.connect: Connection timeout!')
                    raise

                raise

            self.client = client

            Logger.info('RemoteConection.connect: Opening SFTP connection.')
            self.sftp = client.open_sftp()
            client = None

            Logger.info('RemoteConection.connect: All done!')

        finally:
            if client is not None:
                client.close()

    def rename_overwrite(self, old_path, new_path):
        """Move a file atomically, just like with the mv command."""

        Logger.info('RemoteConection.rename_overwrite: Moving file {} to {}'.format(
            old_path, new_path))

        old_path = self.sftp._adjust_cwd(old_path)
        new_path = self.sftp._adjust_cwd(new_path)
        self.sftp._request(CMD_EXTENDED, 'posix-rename@openssh.com', old_path, new_path)

        Logger.info('RemoteConection.rename_overwrite: Done')

    def read_file(self, path):
        """Read and return the file contents."""

        Logger.info('RemoteConection.read_file: Reading file {}'.format(path))

        with self.sftp.file(path, 'rb') as f:
            return f.read()

    def save_file(self, path, contents, keep_backups=10):
        """Save a file contents to a file atomically. Keep backups, optionally.
        The file will be saved to a temporary name and when it is fully
        transferred, it will be renamed to the requested name.
        Old instances of the file may be kept as backup if keep_backups is > 0.
        """

        tmp_path = '{}.tmp{}'.format(path, self._random_str())
        Logger.info('RemoteConection.save_file: Saving data to {} using temporary name {}'.format(
            path, tmp_path))

        with self.sftp.file(tmp_path, 'wb') as f:
            f.write(contents)

        if keep_backups:
            format_backup = lambda x: path + '_bak{}'.format('' if x == 0 else x)

            # Rotate the backups
            for i in range(keep_backups - 1, 0, -1):
                with ignore_nosuchfile_ioerror():
                    self.rename_overwrite(format_backup(i - 1), format_backup(i))

            with ignore_nosuchfile_ioerror():
                self.rename_overwrite(path, format_backup(0))

        self.rename_overwrite(tmp_path, path)
        Logger.info('RemoteConection.save_file: Saved.')

    def put_file(self, local_file_path, remote_file_path):
        """Save a local file to the remote path, atomically.
        The file will be saved to a temporary name and when it is fully
        transferred, it will be renamed to the requested name.
        """

        remote_file_path_tmp = '{}.tmp{}'.format(remote_file_path, self._random_str())
        Logger.info('RemoteConection.put_file: Saving local file {} to {} using temporary name {}'.format(
            local_file_path, remote_file_path, remote_file_path_tmp))
        local_stat = os.stat(local_file_path)

        # Put the file to a temporary name so it doesn't trigger any scripts
        # while it is uploading and in case the transfer fails mid-upload
        remote_stat = self.sftp.put(local_file_path, remote_file_path_tmp, confirm=True)

        if local_stat.st_size != remote_stat.st_size:
            raise Exception("Uploaded file size differs from local file size. Upload failed.")

        # Rename the file to the requested name
        self.rename_overwrite(remote_file_path_tmp, remote_file_path)
        Logger.info('RemoteConection.put_file: Saved.')


    def list_files(self, path):
        """Return the list of files in the path, just like os.listdir()."""

        return self.sftp.listdir(path)

    def remove_file(self, path):
        """Unlink a remote file. Does not work with directories."""

        Logger.info('RemoteConection.remove_file: Removing {}'.format(path))
        self.sftp.unlink(path)
        Logger.info('RemoteConection.remove_file: Removed.')


if __name__ == '__main__':
    pass
    # perform_update('somemod')
