import multiprocessing
from multiprocessing import Queue

from kivy.logger import Logger

from utils.process import Process
from sync.httpsyncer import HttpSyncer



class SubProcess(Process):
    def __init__(self, syncclass, dest, url, resultQueue):
        self.resultQueue = resultQueue
        self.dest = dest
        self.url = url
        self.syncclass = syncclass

        multiprocessing.Process.__init__(self)
        self.start()

    def run(self):
        syncer = self.syncclass(self.dest, self.url, self.resultQueue)
        syncer.sync()


class ModManager(object):
    """docstring for ModManager"""
    def __init__(self):
        super(ModManager, self).__init__()

    def _sync_single_mod(self, mod):
        loc = mod.clientlocation
        url = mod.downloadurl
        syncclass = None

        if mod.synctype == 'http':
            syncclass = HttpSyncer

        Logger.debug('ModManager: syncing mod:' + mod.name)

        self.current_queue = Queue()
        SubProcess(syncclass, loc, url, self.current_queue);

    def query_status(self):
        if not self.current_queue.empty():
            progress = self.current_queue.get_nowait()
            return progress
        else:
            return None
