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

import sys
import os

#
# we have to protect the instantiation of the kivy app, cause
# of the use of multiprocessing. If you spawn a new thread or process
# it loads this file again. So there is the need of the __main__ guard.
#
if __name__ == "__main__":

    # import multiprocessing and enable freeze_support which is neeeded on win
    import multiprocessing
    multiprocessing.freeze_support()

    # initilize settings class
    from utils.settings import Settings
    settings = Settings(sys.argv[1:])

    # HACK: clear sys.argv for kivy. Keep only the first element
    sys.argv = sys.argv[0:1]

    # configure kivy
    from kivy.config import Config

    if not settings.get('self_update'):
        Config.set('graphics','resizable',0)
        Config.set('graphics', 'width', '1000')
        Config.set('graphics', 'height', '666')
        Config.set('graphics','borderless',1)
    else:
        Config.set('graphics','resizable',0)
        Config.set('graphics', 'width', '400')
        Config.set('graphics', 'height', '150')
        Config.set('graphics','borderless',1)

    #
    # other imports
    #
    import kivy
    kivy.require('1.8.0')
    from kivy.app import App
    from kivy.uix.label import Label
    from kivy.uix.widget import Widget
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.button import Button
    from kivy.uix.stacklayout import StackLayout
    from kivy.graphics import Line, Color
    from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty
    from kivy.core.window import Window
    from kivy.clock import Clock
    from kivy.logger import Logger
    from kivy.uix.screenmanager import ScreenManager, Screen

    from utils.app import BaseApp
    from view.hoverbutton import HoverButton
    from view.statusimage import StatusImage
    from gui.mainwidget import MainWidget
    from gui.updatermainwidget import UpdaterMainWidget
    from gui.installscreen import InstallScreen
    import logging

    class PrefScreen(Screen):
        pass

    class MainScreenManager(ScreenManager):
        pass

    class LauncherApp(BaseApp):
        """Main class for the normal app"""
        def __init__(self, settings):
            super(LauncherApp, self).__init__()
            self.settings = settings

        def build(self):
            logger = logging.getLogger('concurrent.futures')
            logger.addHandler(logging.StreamHandler())
            return MainWidget()

    class SelfUpdaterApp(BaseApp):
        """app which starts the self updater"""

        def __init__(self, settings):
            super(SelfUpdaterApp, self).__init__()

        def build(self):
            logger = logging.getLogger('concurrent.futures')
            logger.addHandler(logging.StreamHandler())
            return UpdaterMainWidget()

    if __name__ == '__main__':
        launcher_app = None

        if settings.get('self_update'):
            print 'launching self updater'
            launcher_app = SelfUpdaterApp(settings).run()
        else:
            launcher_app = LauncherApp(settings).run()
