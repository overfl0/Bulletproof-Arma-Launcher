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

    # configure kivy
    from kivy.config import Config
    Config.set('graphics','resizable',0)
    Config.set('graphics', 'width', '1000')
    Config.set('graphics', 'height', '666')
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
    from controller.mainwidget import MainWidgetController
    import logging

    class MainWidget(Widget):
        """
        root widget of the app
        """
        def __init__(self, **kwargs):
            super(MainWidget, self).__init__(**kwargs)
            self.controller = MainWidgetController(self)

    class InstallScreen(Screen):
        pass

    class PrefScreen(Screen):
        pass

    class MainScreenManager(ScreenManager):
        pass

    class LauncherApp(BaseApp):
        """Main class for the normal app"""

        def build(self):
            logger = logging.getLogger('concurrent.futures')
            logger.addHandler(logging.StreamHandler())
            return MainWidget()

    if __name__ == '__main__':
        launcher_app = LauncherApp().run()
