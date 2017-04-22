from __future__ import unicode_literals

"""
Script to get metadata from the server and then optionally print hashes of all
files contained in all torrents served.
"""

import argparse
import os
import json
import libtorrent
import urllib2
import time

from collections import namedtuple

WAIT_TIMEOUT = 6


def check_file(filename):
    """List the files that are inside the torrent file."""

    with open(filename, 'rb') as file_handle:
        file_contents = file_handle.read()

    torrent_metadata = libtorrent.bdecode(file_contents)
    torrent_info = libtorrent.torrent_info(torrent_metadata)

    for file_info in torrent_info.files():
        print file_info.filehash.to_bytes().encode('hex')


def directory_cleanup(files_to_keep):
    print 'Removing superfluous torrents...'
    for filename in os.listdir(args.directory):
        if not filename.endswith('.torrent'):
            continue

        if filename in files_to_keep:
            continue

        filepath = os.path.join(args.directory, filename)
        print 'Deleting {}...'.format(filepath)
        os.unlink(filepath)


def save_files(files):
    print 'Saving new files...'
    for file_obj in files:
        with file(file_obj.path, 'wb') as f:
            f.write(file_obj.contents)


def fetch_files(mods):
    print 'Fetching files into memory...'

    File = namedtuple('File', ['name', 'path', 'contents'])
    files = []

    for mod in mods:
        filename = '{}-{}.torrent'.format(mod['foldername'], mod['torrent-timestamp'])
        torrent_url = '{}torrents/{}'.format(args.bare_url, filename)
        store_path = os.path.join(args.directory, filename)

        print 'Fetching: {}...'.format(torrent_url)
        file_content = urllib2.urlopen(torrent_url).read()
        files.append(File(filename, store_path, file_content))

    return files


def wait_timeout():
    print 'Waiting {} seconds...'.format(args.wait)
    time.sleep(args.wait)


def update_torrents():
    # Fetch the metadata
    json_url = args.bare_url + 'metadata.json'
    print 'Fetching {}...'.format(json_url)
    metadata_json = urllib2.urlopen(json_url).read()
    metadata = json.loads(metadata_json)

    # Get all the mods from the metadata
    mods = [metadata.get('launcher')] if metadata.get('launcher') else []
    mods.extend(metadata.get('mods', []))
    for server in metadata.get('servers', []):
        mods.extend(server.get('mods', []))

    files = fetch_files(mods)
    directory_cleanup([f.name for f in files])
    wait_timeout()
    save_files(files)


def main():
    global args

    parser = argparse.ArgumentParser(description='Update all the local torrent files to match what\'s in metadata.json')
    parser.add_argument('host', help='Domain of the launcher')
    parser.add_argument('-d', '--directory', default='.', help='Torrents directory')
    parser.add_argument('-w', '--wait', type=int, default=WAIT_TIMEOUT, help='Torrents directory')

    args = parser.parse_args()
    args.bare_url = 'http://{}/'.format(args.host)

    assert os.path.isdir(args.directory), '{}: Not a directory'.format(args.directory)

    update_torrents()


if __name__ == '__main__':
    main()


# Sample torrent url:
# http://91.121.120.221/tacbf/updater/torrents/@AllInArmaTerrainPack-2015-05-17_1431885737.torrent
