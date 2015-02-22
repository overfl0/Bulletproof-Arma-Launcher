from multiprocessing import Pool
from sync.httpsyncer import HttpSyncer
from sync.mod import Mod
import os
from time import sleep

import requests

import kivy
from kivy.clock import Clock

class MainWidgetController(object):
    def __init__(self, widget):
        super(MainWidgetController, self).__init__()
        self.view = widget

    def on_install_button_release(self, btn, image):
        app = kivy.app.App.get_running_app()
        print 'button clicked', str(btn), str(image)
        image.source = app.resource_path('images/installing.png')
        print 'MainWidget ids:', self.view.ids
        self.test_file_download()

    def test_file_download(self):

        mod = Mod(
            clientlocation=os.getcwd(),
            downloadurl='http://kivy.org/downloads/1.8.0/Kivy-1.8.0-py2.7-win32.zip')

        s = HttpSyncer()
        future, q = s.sync(mod)
        future.add_done_callback(self.on_download_finish)
        Clock.schedule_interval(self.on_progress, 0.5)
        self.progress_queue = q

    def on_download_finish(self, future):
        print "download finished"
        print 'hello'
        if future.exception():
            raise future.exception()

    def on_progress(self, dt):
        if not self.progress_queue.empty():
            print self.progress_queue.get_nowait()
        else:
            print "queue is empty"
