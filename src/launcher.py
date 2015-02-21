import sys
import os

from kivy.config import Config
Config.set('graphics','resizable',0)
Config.set('graphics', 'width', '1000')
Config.set('graphics', 'height', '666')
Config.set('graphics','borderless',1)
import kivy
kivy.require('1.8.0') # replace with your current kivy version !
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

from view.hoverbutton import HoverButton
from controller.mainwidget import MainWidgetController


class MainWidget(Widget):
    """
    root widget of the app
    """
    def __init__(self, **kwargs):
        super(MainWidget, self).__init__(**kwargs)
        self.controller = MainWidgetController(self)

class LauncherApp(App):

    def build(self):

        # basic
        return MainWidget()

    def resource_path(self, relative):
        """
        This method makes sure that the app can access resource path
        also if packed within a single executable
        """
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, relative)
        return os.path.join('../resources', relative)

if __name__ == '__main__':
    launcher_app = LauncherApp().run()
