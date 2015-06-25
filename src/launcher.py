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

from utils.requirements import check_libraries_requirements

# HACK: clear sys.argv for kivy. Keep only the first element
# Arguments passed to this program are also implicitly passed to processes spawned
# with multiprocessing which make them crash if an argument that is not supported by
# Kivy shows up in the command line.
original_argv = sys.argv
sys.argv = sys.argv[0:1]

# we have to protect the instantiation of the kivy app, cause
# of the use of multiprocessing. If you spawn a new thread or process
# it loads this file again. So there is the need of the __main__ guard.
#
if __name__ == "__main__":
    # Enforce all requirements so that the program doesn't crash in the middle of execution.
    check_libraries_requirements()

    # import multiprocessing and enable freeze_support which is neeeded on win
    import multiprocessing
    multiprocessing.freeze_support()

    # initilize settings class
    from utils.settings import Settings
    settings = Settings(original_argv[1:])

    # configure kivy
    from kivy.config import Config

    if not settings.get('update'):
        Config.set('graphics','resizable',0)
        Config.set('graphics', 'width', 1000)
        Config.set('graphics', 'height', 666)
        Config.set('graphics','borderless',1)
    else:
        Config.set('graphics','resizable',0)
        Config.set('graphics', 'width', 400)
        Config.set('graphics', 'height', 150)
        Config.set('graphics','borderless',1)

    #
    # other imports
    #
    import kivy

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
    from kivy.core.text import LabelBase
    from kivy.base import ExceptionManager

    from utils.app import BaseApp
    from view.hoverbutton import HoverButton
    from view.statusimage import StatusImage
    from view.errorpopup import error_popup_decorator
    from view.errorpopup import PopupHandler
    from gui.mainwidget import MainWidget
    from gui.updatermainwidget import UpdaterMainWidget
    from gui.installscreen import InstallScreen
    import logging

    if settings.get('exc_popup') == True:
        ExceptionManager.add_handler(PopupHandler())

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
            self.settings = settings

        def build(self):
            logger = logging.getLogger('concurrent.futures')
            logger.addHandler(logging.StreamHandler())
            return UpdaterMainWidget()

    if __name__ == '__main__':
        launcher_app = None

        if settings.get('update'):
            print 'launching self updater'
            launcher_app = SelfUpdaterApp(settings).run()

        elif settings.get('run_updated'):
            print 'Updated!'
            sys.exit(0)

        else:
            launcher_app = LauncherApp(settings)
            #launcher_app.run = error_popup_decorator(launcher_app.run)
            launcher_app.run()
