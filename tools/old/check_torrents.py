"""
Script to get metadata from the server and then print hashes of all files
contained in all torrents served.
Unused now but kept for posterity.
"""

import json
import libtorrent
import urllib2

base_url = "http://launcher.tacbf.com/tacbf/updater/"
json_url = base_url + "metadata.json"

metadata_json = urllib2.urlopen(json_url).read()
metadata = json.loads(metadata_json)

# print metadata

def check_file(filename):
    with open(filename, 'rb') as file_handle:
        file_contents = file_handle.read()

    torrent_metadata = libtorrent.bdecode(file_contents)
    torrent_info = libtorrent.torrent_info(torrent_metadata)

    for file_info in torrent_info.files():
        print file_info.filehash.to_bytes().encode("hex")

for mod in metadata["mods"]:
    filename = "{}-{}.torrent".format(mod["foldername"], mod["torrent-timestamp"])
    torrent_url = "{}torrents/{}".format(base_url, filename)
    print torrent_url

    file_content = urllib2.urlopen(torrent_url).read()
    with file(filename, "wb") as f:
        f.write(file_content)

    check_file(filename)

# http://launcher.tacbf.com/tacbf/updater/torrents/@AllInArmaTerrainPack-2015-05-17_1431885737.torrent
