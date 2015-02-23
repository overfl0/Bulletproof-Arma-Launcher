from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Queue, Manager
import multiprocessing
from time import sleep
import logging
import os
import requests
from datetime import datetime

from utils.process import Process

class HttpSyncer(object):
    """
    example syncer implementation

    takes a mod as parameter. See mod class
    """
    def __init__(self, dest, url, result_queue):
        super(HttpSyncer, self).__init__()
        self.url = url
        self.dest = dest
        self.result_queue = result_queue

    def sync(self):
        """
        helper function to download. It needs to be
        on module level since multiprocessing needs
        pickable objects
        """
        #print "downloading ", url, "to:", dest
        sleep(2)
        self.result_queue.put((0.1, 400, 'downloading'))
        sleep(2)
        self.result_queue.put((0.3, 400, 'downloading'))
        sleep(2)
        self.result_queue.put((0.7, 400, 'downloading'))
        sleep(2)
        self.result_queue.put((1.0, 400, 'downloading'))
        # with o    pen(os.path.join(dest, 'kivy.zip'), 'wb') as handle:
        #
        #     #print "get request"
        #     response = requests.get(
        #         url,
        #         stream=True
        #     )
        #
        #     #print "request ready"
        #
        #     # if not response.ok:
        #     #     print 'response failed'
        #
        #     start_time = datetime.now()
        #     length = float(response.headers['content-length'])
        #     #print length
        #     downloaded = 0.0
        #     counter = 0
        #
        #     for block in response.iter_content(1024):
        #         if not block:
        #             break
        #
        #         handle.write(block)
        #         downloaded = downloaded + 1024
        #
        #
        #         if counter >= 1000 and not downloaded < 1:
        #             percent = downloaded / length
        #             td = datetime.now() - start_time
        #             kbpersec = (downloaded / 1024) / td.total_seconds()
        #             q.put((percent, kbpersec, 'downloading'))
        #             counter = 0
        #
        #         counter += 1

        self.result_queue.put((100, 0, 'finished'))
