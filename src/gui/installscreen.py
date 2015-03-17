# Tactical Battlefield Installer/Updater/Launcher
# Copyright (C) 2015 TacBF Installer Team.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

from multiprocessing import Pool
from sync.httpsyncer import HttpSyncer
from sync.mod import Mod
import os
from time import sleep

import requests
import kivy
from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import ScreenManager, Screen

from sync.modmanager import ModManager
from sync.modmanager import get_mod_descriptions
from multiprocessing import Queue, Process

class InstallScreen(Screen):
    """
    View Class
    """
    def __init__(self, **kwargs):
        super(InstallScreen, self).__init__(**kwargs)

        self.statusmessage_map = {
            'moddescdownload': 'Retreiving Mod Descriptions',
            'moddownload': 'Retreiving Mod'
        }

        self.controller = Controller(self)

class Controller(object):
    def __init__(self, widget):
        super(Controller, self).__init__()
        self.view = widget
        self.mod_manager = ModManager()

        # download mod descriptions
        self.messagequeue = Queue()
        self.messagequeue.put({
            'action': 'moddescdownload',
            'status': 'downloading',
            'progress': 0.3,
            'kbpersec': 0.0,})

        p = Process(target=get_mod_descriptions, args=(self.messagequeue,))
        p.start()

        Clock.schedule_interval(self.on_progress, 1.0)

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

        self.view.ids.status_label.text = 'Downloading mod ' + mod.name + ' ...'

        self.mod_manager._sync_single_mod(mod)

        Clock.schedule_interval(self.on_progress, 0.5)

    def on_download_finish(self):
        print "download finished"
        print 'hello'

        self.view.ids.status_label.text = 'Download finished.'
        self.view.ids.progress_bar.value = 100


    def on_progress(self, dt):
        queue = self.messagequeue
        progress = None

        if not queue.empty():
            progress = queue.get_nowait()

        if progress:
            print 'Got progress: ', progress
            self.view.ids.progress_bar.value = progress['progress'] * 100

            if progress['status'] == 'downloading':
                self.view.ids.status_label.text = self.view.statusmessage_map[progress['action']]
            elif progress['status'] == 'finished':
                self.view.ids.status_label.text = self.view.statusmessage_map[progress['action']] + ' Finished'
                Clock.unschedule(self.on_progress)

                if 'data' in progress:
                    print 'we got data', progress['data']

        else:
            print "queue is empty"
