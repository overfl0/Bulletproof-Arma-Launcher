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
        height = image.height
        btn.disabled = True
        image.source = app.resource_path('images/installing.png')
        image.height = height
        print 'MainWidget ids:', self.view.ids
        self.test_file_download()

    def test_file_download(self):

        self.view.ids.status_label.text = 'Downloading...'

        mod = Mod(
            name='@kivybattle',
            clientlocation=os.getcwd(),
            downloadurl='http://kivy.org/downloads/1.8.0/Kivy-1.8.0-py2.7-win32.zip')

        self.view.ids.status_label.text = 'Downloading mod ' + mod.name + ' ...'

        s = HttpSyncer()
        q = s.sync(mod)
        self.progress_queue = q
        Clock.schedule_interval(self.on_progress, 0.5)

    def on_download_finish(self):
        print "download finished"
        print 'hello'

        self.view.ids.status_label.text = 'Download finished.'
        self.view.ids.progress_bar.value = 100

        Clock.unschedule(self.on_progress)


    def on_progress(self, dt):
        if not self.progress_queue.empty():
            progress = self.progress_queue.get_nowait()
            self.view.ids.progress_bar.value = progress[0] * 100

            if progress[2] == 'finished':
                self.on_download_finish()
        else:
            print "queue is empty"
