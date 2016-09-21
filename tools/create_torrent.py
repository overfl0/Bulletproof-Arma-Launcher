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


def create_dummy_file(filename, size_mb):
    with open(filename, "wb") as file_handle:
        value = "A" * 1024 * 1024
        for i in xrange(size_mb):
            file_handle.write(value)


def create_dumy_torrent_file_with_dir(size):
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


def create_torrent(directory, announces=None, output=None, comment=None, web_seeds=None):
    if not output:
        output = directory + ".torrent"

    # "If a piece size of 0 is specified, a piece_size will be calculated such that the torrent file is roughly 40 kB."
    piece_size_multiplier = 0
    piece_size = (16 * 1024) * piece_size_multiplier  # Must be multiple of 16KB

    # http://www.libtorrent.org/make_torrent.html#create-torrent
    flags = libtorrent.create_torrent_flags_t.calculate_file_hashes

    if not os.path.isdir(directory):
        raise Exception("The path {} is not a directory".format(directory))

    fs = libtorrent.file_storage()
    libtorrent.add_files(fs, directory, flags=flags)
    t = libtorrent.create_torrent(fs, piece_size=piece_size, flags=flags)

    for announce in announces:
        t.add_tracker(announce)

    if comment:
        t.set_comment(comment)

    for web_seed in web_seeds:
        t.add_url_seed(web_seed)
    # t.add_http_seed("http://...")

    libtorrent.set_piece_hashes(t, os.path.dirname(directory))

    with open(output, "wb") as file_handle:
        file_handle.write(libtorrent.bencode(t.generate()))


def main():
    parser = argparse.ArgumentParser(description="Creates a torrent from a directory.")
    parser.add_argument("-a", "--announce", required=True, action='append', help="Full announce URL. Additional -a add backup trackers")
    parser.add_argument("-c", "--comment", help="Add a comment to the metainfo")
    parser.add_argument("-o", "--output", help="Set the path and the filename of the created file")
    parser.add_argument("-w", "--web-seed", action='append', default=[], help="Set the web-seed (url-seed as explained in BEP 19). Additional -w add more urls")
    parser.add_argument("directory", help="Data directory")
    # parser.add_argument("-s", "--size", type=int, help="Create a DUMMY torrent of <size>MB. <directory> will be overwritten!", default=50)

    args = parser.parse_args()

    create_torrent(directory=args.directory, announces=args.announce, comment=args.comment,
                   output=args.output, web_seeds=args.web_seed)

    # create_dumy_torrent_file_with_dir(args.size)

if __name__ == "__main__":
    main()
