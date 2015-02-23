import multiprocessing
from multiprocessing import Queue

from kivy.logger import Logger

from utils.process import Process
from sync.httpsyncer import HttpSyncer

class SubProcess(Process):
    def __init__(self, syncclass, resultQueue, mod):
        self.resultQueue = resultQueue
        self.syncclass = syncclass
        self.mod = mod

        multiprocessing.Process.__init__(self)
        self.start()

    def run(self):
        syncer = self.syncclass(self.resultQueue, self.mod)
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
        SubProcess(syncclass, self.current_queue, mod);

    def _check_already_installed_with_six(self, mod):
        pass

    def _get_arma_folders(self):
        pass

    def _get_remote_mod_list(self):
        pass

    def sync_all(self):
        pass

    def query_status(self):
        if not self.current_queue.empty():
            progress = self.current_queue.get_nowait()
            return progress
        else:
            return None
