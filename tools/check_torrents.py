from __future__ import unicode_literals

"""
Script to get metadata from the server and then optionally print hashes of all
files contained in all torrents served.
"""

import os
import json
import libtorrent
import urllib2
import sys
import time

from collections import namedtuple

WAIT_TIMEOUT = 6


store_base = '.'
if len(sys.argv) > 1:
    store_base = sys.argv[1]

assert os.path.isdir(store_base), "{}: Not a directory".format(store_base)

domain = 'launcher.frontline.frl'
host = 'http://{}/'.format(domain)

json_url = host + "metadata.json"
metadata_json = urllib2.urlopen(json_url).read()
metadata = json.loads(metadata_json)

def check_file(filename):
    """List the files that are inside the torrent file."""

    with open(filename, 'rb') as file_handle:
        file_contents = file_handle.read()

    torrent_metadata = libtorrent.bdecode(file_contents)
    torrent_info = libtorrent.torrent_info(torrent_metadata)

    for file_info in torrent_info.files():
        print file_info.filehash.to_bytes().encode("hex")


def directory_cleanup(files_to_keep, directory='.'):
    print 'Removing superfluous torrents...'
    for filename in os.listdir(directory):
        if not filename.endswith('.torrent'):
            continue

        if filename in files_to_keep:
            continue

        filepath = os.path.join(directory, filename)
        os.unlink(filepath)


def save_files(files):
    print 'Saving new files...'
    for file_obj in files:
        with file(file_obj.path, "wb") as f:
            f.write(file_obj.contents)


def fetch_files(mods):
    print 'Fetching files into memory...'

    File = namedtuple('File', ['name', 'path', 'contents'])
    files = []

    for mod in mods:
        filename = "{}-{}.torrent".format(mod["foldername"], mod["torrent-timestamp"])
        torrent_url = "{}torrents/{}".format(host, filename)
        store_path = os.path.join(store_base, filename)
        print torrent_url

        file_content = urllib2.urlopen(torrent_url).read()
        files.append(File(filename, store_path, file_content))

    return files


def wait_timeout():
    print 'Waiting {} seconds...'.format(WAIT_TIMEOUT)
    time.sleep(WAIT_TIMEOUT)


def main():
    # Get all the mods from the metadata
    mods = [metadata.get('launcher')] if metadata.get('launcher') else []
    mods.extend(metadata.get('mods', []))
    for server in metadata.get('servers', []):
        mods.extend(server.get('mods', []))

    files = fetch_files(mods)
    directory_cleanup([f.name for f in files], store_base)
    wait_timeout()
    save_files(files)


if __name__ == '__main__':
    main()


# Sample torrent url:
# http://91.121.120.221/tacbf/updater/torrents/@AllInArmaTerrainPack-2015-05-17_1431885737.torrent
