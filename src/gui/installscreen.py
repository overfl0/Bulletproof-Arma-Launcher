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

from multiprocessing import Queue


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
from sync.httpsyncer import HttpSyncer
from sync.mod import Mod
from utils.process import Process

class InstallScreen(Screen):
    """
    View Class
    """
    def __init__(self, **kwargs):
        super(InstallScreen, self).__init__(**kwargs)

        self.statusmessage_map = {
            'moddescdownload': 'Retreiving Mod Descriptions',
            'checkmods': 'Checking Mods',
            'moddownload': 'Retreiving Mod',
            'syncing': 'Syncing Mods'
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
        p = Process(target=self.mod_manager.prepare_and_check, args=(self.messagequeue,))
        p.start()
        self.current_child_process = p

        Clock.schedule_interval(self.handle_messagequeue, 1.0)

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
        self.messagequeue = Queue()
        p = Process(target=self.mod_manager.sync_all, args=(self.messagequeue,))
        p.start()
        self.current_child_process = p

    def on_checkmods_inprogress(self, progress):
        print 'checkmods in progress'

    def on_checkmods_finished(self, progress):
        print 'checkmods finshed'
        self.current_child_process.join()
        self.view.ids.install_button.disabled = False

    def on_syncing_inprogress(self, progress):
        print 'syncing in progress'

    def on_syncing_finished(self, progress):
        print 'syncing finshed'
        self.current_child_process.join()
        Clock.unschedule(self.handle_messagequeue)

    def handle_messagequeue(self, dt):
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

                funcname = 'on_' + progress['action'] + '_inprogress'
                func = getattr(self, funcname , None)
                if callable(func):
                    func(progress)

            elif progress['status'] == 'finished':
                self.view.ids.status_label.text = self.view.statusmessage_map[progress['action']] + ' Finished'
                funcname = 'on_' + progress['action'] + '_finished'
                func = getattr(self, funcname , None)
                print 'calling function', funcname, func
                if callable(func):
                    func(progress)

                if 'data' in progress:
                    print 'we got data', progress['data']

        else:
            print "queue is empty"
