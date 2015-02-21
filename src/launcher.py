from kivy.config import Config
Config.set('graphics','resizable',0)
Config.set('graphics', 'width', '1000')
Config.set('graphics', 'height', '666')
Config.set('graphics','borderless',1)

import kivy
import sys
import os

kivy.require('1.8.0') # replace with your current kivy version !

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.stacklayout import StackLayout
from kivy.graphics import Line, Color
from kivy.properties import NumericProperty, ObjectProperty, BooleanProperty, StringProperty
from borderbehavior import BorderBehavior
from kivy.core.window import Window
from kivy.clock import Clock





class MyButton(Button):
    """
    lightly extended button implementation

    It supports hover state for now
    """
    mouse_hover = BooleanProperty(False)
    background_hover = StringProperty('')

    def __init__(self, **kwargs):
        super(MyButton, self).__init__(**kwargs)
        Window.bind(mouse_pos=self.check_hover)

        self.background_normal_orig = ''

    def check_hover(self, instance, value):

        if (self.x <= value[0] <= self.x + self.width and
            self.y <= value[1] <= self.y + self.height):

            if self.mouse_hover == False:
                self.mouse_hover = True

        elif self.mouse_hover == True:
            self.mouse_hover = False

    def on_mouse_hover(self, instance, value):
        print 'mouse_hover changed', value
        if (value == True):
            print 'switching to bg hover', self.background_hover
            self.background_normal_orig = self.background_normal
            self.background_normal = self.background_hover
        else:
            self.background_normal = self.background_normal_orig



class MainWidget(Widget):
    def __init__(self, **kwargs):
        super(MainWidget, self).__init__(**kwargs)

    def on_install_button_release(self, btn, image):
        app = kivy.app.App.get_running_app()
        print 'button clicked', str(btn), str(image)
        image.source = app.resource_path('images/installing.png')
        print 'MainWidget ids:', self.ids



class LauncherApp(App):

    def build(self):

        # basic
        return MainWidget()

    def resource_path(self, relative):
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, relative)
        return os.path.join('../resources', relative)






if __name__ == '__main__':
    launcher_app = LauncherApp().run()
