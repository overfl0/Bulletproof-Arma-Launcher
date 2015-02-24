from time import sleep
import libtorrent

class TorrentSyncer(object):
    """
    Bittorrent Proof Of Concept syncer implementation

    the class basically gets a message queue where it has to communicate
    its status back. This is done via an dict object looking like:

    msg = {
        status: 'downloading',
        progress: 0.5,
        kbpersec: 280
    }

    status:
        could be: 'downloading', 'finished', 'error'

    progress:
        percentage progress from 0 to 1 as float
        or None to indicate that progress bar is not possible

    kbpersec:
        download rate in kilobyte per seconds or None if
        its not possible to calculate the rate

    The reason for the message queue is multiprocessing
    """

    _update_interval = 1

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

    def sync(self):
        """
        helper function to download. It needs to be
        on module level since multiprocessing needs
        pickable objects
        """
        """Attention!
        This is just a proof of concept module for now.
        No extensive checks are performed! This module is the definition of wishful thinking.
        """

        print "downloading ", self.mod.downloadurl, "to:", self.mod.clientlocation
        print "TODO: Download this to a temporary location and copy/move afterwards"

        session = libtorrent.session()
        session.listen_on(6881, 6891)

        torrent_data = libtorrent.bdecode(open(self.mod.downloadurl, 'rb').read())
        torrent_info = libtorrent.torrent_info(torrent_data)

        params = {
            'save_path': self.mod.clientlocation,
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

            self.result_queue.put({
                'progress': download_fraction,
                'kbpersec': download_kbs,
                'status': str(s.state)})
            sleep(self._update_interval)

        self.result_queue.put({
            'progress': 1.0,
            'kbpersec': 0,
            'status': 'finished'})
