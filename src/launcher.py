# Bulletproof Arma Launcher
# Copyright (C) 2016 Sascha Ebert
# Copyright (C) 2017 Lukasz Taczuk
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

from __future__ import unicode_literals
from utils.paths import fix_unicode_paths
fix_unicode_paths()


def start():
    """This is the main function that is called unconditionally.
    Unconditionally means, regardless of whether __name__ == '__main__' or not.

    It is all a mess but with historical reasons where imports had to be in the
    right order :).

    It would be nice to refactor it one day.
    """

    # Enforce all requirements so that the program doesn't crash in the middle of execution.
    if __name__ == '__main__':
        from utils.requirements import check_libraries_requirements
        check_libraries_requirements()

    # Import multiprocessing and enable freeze_support which is needed on windows
    import multiprocessing
    multiprocessing.freeze_support()

    # Import kivy as soon as possible to let it eat all the kivy args from sys.argv
    import kivy

    #
    # we have to protect the instantiation of the kivy app, cause
    # of the use of multiprocessing. If you spawn a new thread or process
    # it loads this file again. So there is the need of the __main__ guard.
    #
    if __name__ == "__main__":
        import sys

        # initialize settings class
        from utils.settings import Settings
        settings = Settings(sys.argv[1:])

        import launcher_config

        # HACK: clear sys.argv for kivy. Keep only the first element
        # sys.argv = sys.argv[0:1]

        # configure kivy
        from kivy import resources
        from kivy.config import Config
        from utils.paths import (
            get_common_resources_path,
            get_resources_path,
            get_source_path,
        )
        from utils.devmode import devmode

        default_log_level = devmode.get_log_level('info')

        resources.resource_add_path(get_common_resources_path())
        resources.resource_add_path(get_source_path())
        resources.resource_add_path(get_resources_path())

        Config.set('kivy', 'window_icon', get_resources_path(launcher_config.icon))
        Config.set('kivy', 'log_level', default_log_level)
        Config.set('input', 'mouse', 'mouse,disable_multitouch')

        if not settings.get('update'):
            Config.set('graphics', 'resizable', 0)
            Config.set('graphics', 'width', 1000)
            Config.set('graphics', 'height', 666)
            Config.set('graphics', 'borderless', 0)
        else:
            Config.set('graphics', 'resizable', 0)
            Config.set('graphics', 'width', 400)
            Config.set('graphics', 'height', 150)
            Config.set('graphics', 'borderless', 1)

        #
        # other imports
        #
        from kivy.app import App
        from kivy.uix.label import Label
        from kivy.uix.widget import Widget
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.button import Button
        from kivy.uix.rst import RstDocument
        from kivy.uix.stacklayout import StackLayout
        from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem, TabbedPanelStrip, TabbedPanelHeader
        from kivy.graphics import Line, Color
        from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty
        from kivy.core.window import Window
        from kivy.clock import Clock
        from kivy.logger import Logger
        from kivy.uix.screenmanager import ScreenManager, Screen
        from kivy.core.text import LabelBase
        from kivy.base import ExceptionManager

        from utils.app import BaseApp
        from view.numberinput import NumberInput
        from view.dynamicbutton import DynamicButton
        from view.hoverbutton import HoverButton
        from view.statusimage import StatusImage
        from view.errorpopup import error_popup_decorator
        from view.errorpopup import PopupHandler
        from view.modlist import ModList
        from view.serverlist import ServerListScrolled
        from view.simplewidgets import CheckLabel

        from gui.mainwidget import MainWidget
        from gui.updatermainwidget import UpdaterMainWidget
        from gui.installscreen import InstallScreen
        from gui.prefscreen import PrefScreen

        import logging

        Logger.info('Para: Starting MAIN PROCESS')

        if settings.get('use_exception_popup') == True:
            ExceptionManager.add_handler(PopupHandler())

        class MainScreenManager(ScreenManager):
            pass

        class LauncherApp(BaseApp):
            """Main class for the normal app"""

            title = launcher_config.launcher_name.encode('utf-8')

            def __init__(self, settings):
                super(LauncherApp, self).__init__()
                self.settings = settings

            def build(self):
                logger = logging.getLogger(__name__)
                logger.addHandler(logging.StreamHandler())
                return MainWidget()

        class SelfUpdaterApp(BaseApp):
            """app which starts the self updater"""

            title = '{} updater'.format(launcher_config.launcher_name).encode('utf-8')

            def __init__(self, settings):
                super(SelfUpdaterApp, self).__init__()
                self.settings = settings

            def build(self):
                logger = logging.getLogger(__name__)
                logger.addHandler(logging.StreamHandler())
                return UpdaterMainWidget()

        if __name__ == '__main__':
            launcher_app = None

            if settings.get('update'):
                print 'launching self updater'
                launcher_app = SelfUpdaterApp(settings).run()

            else:
                launcher_app = LauncherApp(settings)
                launcher_app.run = error_popup_decorator(launcher_app.run)
                launcher_app.run()


# Mega catch-all. This is ugly but probably the only way to show users a message
# in any possible case something fails at any possible place.
try:
    # Workaround for unicode exceptions that don't ever tell you WHAT caused them
    try:
        # Call this unconditionally
        start()

    except (UnicodeEncodeError, UnicodeDecodeError) as ex:
        import sys
        error_message = "{}. Original exception: {} Text: {}".format(unicode(ex), type(ex).__name__, repr(ex.args[1]))
        raise UnicodeError, UnicodeError(error_message), sys.exc_info()[2]

except Exception:
    # Mega catch-all requirements
    # Try to catch all possible problems
    import sys
    exc_info = sys.exc_info()

    from utils.critical_messagebox import MessageBox

    CRITICAL_POPUP_TITLE = """An error occurred. Copy it with Ctrl+C and submit a bug"""
    try:
        from utils.primitive_git import get_git_sha1_auto
        build = get_git_sha1_auto()

    except:
        build = 'N/A (exception occurred)\nBuild exception reason:\n{}'.format(
            repr(sys.exc_info()[1])
        )

    try:
        from utils.testtools_compat import _format_exc_info
        stacktrace = "".join(_format_exc_info(*exc_info))

    except:
        try:
            import traceback
            last_chance_traceback = "\n".join(traceback.format_tb(exc_info[2]))

        except:
            last_chance_traceback = "Traceback parsing failed. Reason:\n{}\n\nLast chance parsing:\n{}".format(
                repr(sys.exc_info()[1]), repr(exc_info[1])
            )

        stacktrace = "Could not parse stacktrace. Emergency parsing:\n{}\nException while parsing stacktrace:\n{}".format(
            last_chance_traceback, repr(sys.exc_info()[1])
        )

    msg = 'Build: {}\n\n{}'.format(build, stacktrace)
    MessageBox(msg, CRITICAL_POPUP_TITLE)
