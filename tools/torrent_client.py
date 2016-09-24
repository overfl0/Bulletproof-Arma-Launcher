#!/usr/bin/env python

# Bulletproof Arma Launcher
# Copyright (C) 2016 Lukasz Taczuk
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import argparse
import libtorrent
import os
import time


def print_session_logs(session):
    alerts = session.pop_alerts()
    for alert in alerts:
        print "Message:", alert.message()


def download_torrent(torrent_file, download_throttle, upload_throttle):
    global torrent_handle
    settings = libtorrent.session_settings()
    settings.user_agent = 'Torrent_launcher_simple_client (libtorrent/{})'.format(libtorrent.version)

    session = libtorrent.session()
    session.listen_on(6881, 6891)
    session.set_settings(settings)

    if upload_throttle is not None:
        session.set_upload_rate_limit(int(upload_throttle) * 1024)

    if download_throttle is not None:
        session.set_download_rate_limit(int(download_throttle) * 1024)

    with open(torrent_file, 'rb') as file_handle:
        file_contents = file_handle.read()

    torrent_metadata = libtorrent.bdecode(file_contents)
    torrent_info = libtorrent.torrent_info(torrent_metadata)

    params = {'save_path': os.getcwd(),
              'storage_mode': libtorrent.storage_mode_t.storage_mode_allocate,  # Reduce fragmentation on disk
              'ti': torrent_info
              }

    torrent_handle = session.add_torrent(params)

    while True:
        s = torrent_handle.status()

        print "{} | {:.2%}\tUpload: {}KB\tDownload: {}KB".format(
            s.state, s.progress, s.upload_rate / 1024, s.download_rate / 1024)

        print_session_logs(session)
        time.sleep(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Simple torrent client. Will download and seed until Ctrl+C is pressed.")
    parser.add_argument("-u", "--upload", help="Upload throttle in KB/s")
    parser.add_argument("-d", "--download", help="Download throttle in KB/s")
    parser.add_argument("torrent_file", help="Torrent file to use.")

    args = parser.parse_args()

    try:
        download_torrent(args.torrent_file, args.download, args.upload)
    except KeyboardInterrupt:
        pass
