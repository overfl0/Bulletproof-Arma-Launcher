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


import paramiko
import posixpath
import socket
import time

from paramiko.sftp import CMD_EXTENDED
from utils.devmode import devmode
from utils.context import ignore_nosuchfile_ioerror

host = devmode.get_server_host(mandatory=True)
username = devmode.get_server_username(mandatory=True)
password = devmode.get_server_password(mandatory=True)
port = devmode.get_server_port(22)
metadata_path = devmode.get_server_metadata_path(mandatory=True)
torrents_path = devmode.get_server_torrents_path(mandatory=True)


class RemoteMissingKeyPolicy(paramiko.client.MissingHostKeyPolicy):
    def __init__(self, *args, **kwargs):
        super(RemoteMissingKeyPolicy, self).__init__(*args, **kwargs)

    def missing_host_key(self, client, hostname, key):
        print "Missing key: ", client, hostname, type(key.get_fingerprint())
        print type(key)
        print dir(key)

        print "Accepting it."
        return


class RemoteConection(object):
    def __init__(self, *args, **kwargs):
        super(RemoteConection, self).__init__(*args, **kwargs)

        self.client = None
        self.sftp = None

    def close(self):
        if self.client is not None:
            self.client.close()
            self.client = None
            self.sftp = None

    def connect(self):
        self.close()

        client = None
        try:
            client = paramiko.client.SSHClient()
            client.load_system_host_keys()
            # client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.set_missing_host_key_policy(RemoteMissingKeyPolicy())
            # TODO: store the server key somewhere after the first connection!
            # and don't use AutoAddPolicy

            try:
                print 'Connecting...'
                client.connect(host, username=username, password=password, port=port, timeout=5)

            except paramiko.BadHostKeyException:
                raise

            except paramiko.AuthenticationException:
                raise

            except paramiko.SSHException:
                raise

            except socket.error as ex:
                if ex.errno == 10060:
                    print 'Connection timeout!'
                    raise

                raise

            self.client = client
            self.sftp = client.open_sftp()
            client = None

        finally:
            if client is not None:
                client.close()

    def rename_overwrite(self, old_path, new_path):
        old_path = self.sftp._adjust_cwd(old_path)
        new_path = self.sftp._adjust_cwd(new_path)
        self.sftp._request(CMD_EXTENDED, 'posix-rename@openssh.com', old_path, new_path)

    def fetch_file(self, path):
        with self.sftp.file(path, 'rb') as f:
            return f.read()

    def save_file(self, path, contents, keep_backups=10):
        tmp_path = path + '_tmp'

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

    def list_files(self, path):
        return self.sftp.listdir(path)

    def remove_file(self, path):
        self.sftp.unlink(path)
        print 'Removed {}'.format(path)


def perform_update(mod_name):  # , new_mod_torrent_path):
    connection = RemoteConection()
    connection.connect()

    try:
        metadata_json_path = posixpath.join(metadata_path, 'metadata.json')
        print metadata_json_path

        # Fetch metadata.json
        metadata_json = connection.fetch_file(metadata_json_path)
        print metadata_json

        # Delete old torrents
        for file_name in connection.list_files(torrents_path):
            if not file_name.endswith('.torrent'):
                continue

            if not file_name.startswith(mod_name):
                continue

            # Got the file[s] to remove
            file_path = posixpath.join(torrents_path, file_name)
            connection.remove_file(file_path)

        # Sleep custom amount of time
        time.sleep(devmode.get_server_torrent_timeout(0))

        # Push new torrents
        # remote_torrent_path = posixpath.join(torrents_path, torrent_name)
        # file_attributes = connection.sftp.put(new_mod_torrent_path, remote_torrent_path, confirm=True)

        # Push modified metadata.json
        connection.save_file(metadata_json_path, metadata_json)

    finally:
        connection.close()


if __name__ == '__main__':
    perform_update('somemod')





