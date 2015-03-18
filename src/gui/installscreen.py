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
from kivy.uix.image import Image

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
            'checkmods': 'Checking Mods',
            'moddownload': 'Retreiving Mod'
        }

        self.controller = Controller(self)

class Controller(object):
    def __init__(self, widget):
        super(Controller, self).__init__()
        self.view = widget
        self.mod_manager = ModManager()
        self.loading_gif = None

        # download mod descriptions
        self.messagequeue = Queue()
        p = Process(target=self.mod_manager.sync_all, args=(self.messagequeue,))
        p.start()
        self.current_child_process = p

        Clock.schedule_interval(self.on_progress, 1.0)

    def show_loading_gif(self, show):
        """
        show the loading gif besides the status_label

        the show parameter should be true to show the image otherwise False
        """
        # TODO: detect image in container
        # see http://stackoverflow.com/questions/24781248/kivy-how-to-get-widget-by-id-without-kv
        # write helper function for this
        app = kivy.app.App.get_running_app()
        image_source = app.resource_path('images/ajax-loader.gif')
        image_container = self.view.ids.loading_image_container

        if show == True and not self.loading_gif:
            image = Image(source=image_source, id='loading_gif')
            image_container.add_widget(image)
            self.loading_gif = image
        elif show == False:
            image_container.remove_widget(self.loading_gif)
            self.loading_gif = None

        print 'added widget', image_container.children

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

            if progress['status'] == 'inprogress':
                text = ""

                if 'msg' in progress:
                    text = progress['msg']
                else:
                    text = self.view.statusmessage_map[progress['action']]

                self.view.ids.status_label.text = text
                self.show_loading_gif(True)

            elif progress['status'] == 'finished':
                self.view.ids.status_label.text = self.view.statusmessage_map[progress['action']] + ' Finished'
                # Clock.unschedule(self.on_progress)
                # self.current_child_process.join()

                if 'data' in progress:
                    print 'we got data', progress['data']

        else:
            print "queue is empty"
