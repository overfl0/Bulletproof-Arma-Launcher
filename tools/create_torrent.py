#!/usr/bin/env python

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

import argparse
import libtorrent
import os

def create_dummy_file(filename, size_mb):
    with open(filename, "wb") as file_handle:
        value = "A" * 1024 * 1024
        for i in xrange(size_mb):
            file_handle.write(value)

def create_torrent_file_with_dir(size):
    print "Creating directory and file with the size of {}MB...".format(size)
    name = str(size) + "MB"

    try:
        os.mkdir(name)
    except OSError as e:
        if e.errno != 17:  # File exists
            raise

    filename = os.path.join(name, name + ".file")

    create_dummy_file(filename, size)
    create_torrent(name)

def create_torrent(directory, name=None):
    if not name:
        name = directory + ".torrent"

    # "If a piece size of 0 is specified, a piece_size will be calculated such that the torrent file is roughly 40 kB."
    piece_size_multiplier = 0
    piece_size = (16 * 1024) * piece_size_multiplier  # Must be multiple of 16KB

    fs = libtorrent.file_storage()
    libtorrent.add_files(fs, directory)
    t = libtorrent.create_torrent(fs, piece_size=piece_size)

    t.add_tracker("http://127.0.0.1:8080/announce")
    #t.add_url_seed("http://...")
    #t.add_http_seed("http://...")

    #libtorrent.set_piece_hashes(t, ".")
    libtorrent.set_piece_hashes(t, os.path.dirname(directory))

    with open(name, "wb") as file_handle:
        file_handle.write(libtorrent.bencode(t.generate()))


def main():
    parser = argparse.ArgumentParser(description="Create a file of <size>MB in a directory and make a torrent out of it.")
    parser.add_argument("-s", "--size", type=int, help="size of the torrent to create (in MB)", default=50)
    parser.add_argument("-d", "--directory", help="directory to convert to torrent")

    args = parser.parse_args()

    if args.directory:
        create_torrent(args.directory)
    else:
        create_torrent_file_with_dir(args.size)

if __name__ == "__main__":
    main()
