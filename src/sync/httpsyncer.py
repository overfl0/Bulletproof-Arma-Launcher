from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Queue, Manager
from time import sleep
import logging
import os
import requests
from datetime import datetime

def download(dest, url, q):
    """
    helper function to download. It needs to be
    on module level since multiprocessing needs
    pickable objects
    """
    print "downloading ", url, "to:", dest
    # sleep(2)
    # q.put(25)
    # sleep(2)
    # q.put(50)
    # sleep(2)
    # q.put(75)
    # sleep(2)
    # q.put(100)
    with open(os.path.join(dest, 'kivy.zip'), 'wb') as handle:

        #print "get request"
        response = requests.get(
            url,
            stream=True
        )

        #print "request ready"

        # if not response.ok:
        #     print 'response failed'

        start_time = datetime.now()
        length = float(response.headers['content-length'])
        print length
        downloaded = 0.0
        counter = 0

        for block in response.iter_content(1024):
            if not block:
                break

            handle.write(block)
            downloaded = downloaded + 1024


            if counter >= 1000 and not downloaded < 1:
                percent = downloaded / length
                td = datetime.now() - start_time
                kbpersec = (downloaded / 1024) / td.total_seconds()
                q.put((percent, kbpersec))
                counter = 0

            counter += 1

class HttpSyncer(object):
    """
    example syncer implementation

    takes a mod as parameter. See mod class
    """
    def __init__(self):
        super(HttpSyncer, self).__init__()

    def sync(self, mod):

        loc = mod.clientlocation
        url = mod.downloadurl

        q = Manager().Queue()
        executor = ProcessPoolExecutor(max_workers=1)
        future = executor.submit(download, loc, url, q)

        return future, q
