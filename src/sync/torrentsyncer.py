from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Queue, Manager
from datetime import datetime
from time import sleep
import libtorrent
import logging
import os
import requests


def download(dest, url, q):
    """
    helper function to download. It needs to be
    on module level since multiprocessing needs
    pickable objects
    """
    """Attention!
    This is just a proof of concept module for now.
    No extensive checks are performed! This module is the definition of wishful thinking.
    """

    print "downloading ", url, "to:", dest

    session = libtorrent.session()
    session.listen_on(6881, 6891)

    torrent_data = libtorrent.bdecode(open(url, 'rb').read())
    torrent_info = libtorrent.torrent_info(torrent_data)

    params = {
        'save_path': dest,
        'storage_mode': libtorrent.storage_mode_t.storage_mode_sparse,
        'ti': torrent_info
    }
    torrent_handle = session.add_torrent(params)

    while (not torrent_handle.is_seed()):
        s = torrent_handle.status()

        download_fraction = s.progress
        download_kbs = s.download_rate / 1024

        state_str = ['queued', 'checking', 'downloading metadata', 'downloading', 'finished', 'seeding', 'allocating']
        print '%.2f%% complete (down: %.1f kB/s up: %.1f kB/s peers: %d) %s' % \
            (s.progress * 100, s.download_rate / 1024, s.upload_rate / 1024, \
            s.num_peers, s.state)

        q.put((download_fraction, download_kbs))
        sleep(1)


class TorrentSyncer(object):
    """
    Bittorrent Proof Of Concept syncer implementation

    takes a mod as parameter. See mod class
    """
    def __init__(self):
        super(TorrentSyncer, self).__init__()

    def sync(self, mod):

        loc = mod.clientlocation
        url = mod.downloadurl

        q = Manager().Queue()
        executor = ProcessPoolExecutor(max_workers=1)
        future = executor.submit(download, loc, url, q)

        return future, q
