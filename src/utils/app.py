import sys, os

from kivy.app import App

class BaseApp(App):
    """docstring for BaseApp"""
    def __init__(self):
        super(BaseApp, self).__init__()

    def resource_path(self, relative):
        """
        This method makes sure that the app can access resource path
        also if packed within a single executable
        """
        if hasattr(sys, "_MEIPASS"):
            return os.path.join(sys._MEIPASS, relative)
        return os.path.join('../resources', relative)
