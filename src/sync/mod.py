
class Mod(object):
    """encapsulate data needed for a mod"""
    def __init__(
            self,
            clientlocation=None,
            synctype='http',
            downloadurl=None):
        super(Mod, self).__init__()

        self.clientlocation = clientlocation
        self.synctype = synctype
        self.downloadurl = downloadurl
