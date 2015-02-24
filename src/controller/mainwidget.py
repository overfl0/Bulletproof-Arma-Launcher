from multiprocessing import Pool
from sync.httpsyncer import HttpSyncer
from sync.torrentsyncer import TorrentSyncer
from sync.mod import Mod
import os
from time import sleep

import requests
import kivy
from kivy.clock import Clock

from sync.modmanager import ModManager

class MainWidgetController(object):
    def __init__(self, widget):
        super(MainWidgetController, self).__init__()
        self.view = widget

        self.mod_manager = ModManager()

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
            name='@CBA_A3',
            clientlocation=os.getcwd(),
            synctype='http',
            downloadurl='http://dev.withsix.com/attachments/download/22231/CBA_A3_RC4.7z');
		"""mod = Mod(
            name='@debussybattle',
            clientlocation=os.getcwd(),
			synctype='torrent',
            downloadurl='test.torrent')"""

        self.view.ids.status_label.text = 'Downloading mod ' + mod.name + ' ...'

        self.mod_manager._sync_single_mod(mod)

        Clock.schedule_interval(self.on_progress, 0.5)

    def on_download_finish(self):
        print "download finished"
        print 'hello'

        self.view.ids.status_label.text = 'Download finished.'
        self.view.ids.progress_bar.value = 100

        Clock.unschedule(self.on_progress)

    def on_progress(self, dt):
        progress = self.mod_manager.query_status()
        if progress:
            self.view.ids.progress_bar.value = progress['progress'] * 100

            if progress['status'] == 'finished':
                self.on_download_finish()
        else:
            print "queue is empty"
