import kivy

class MainWidgetController(object):
    def __init__(self, widget):
        super(MainWidgetController, self).__init__()
        self.view = widget

    def on_install_button_release(self, btn, image):
        app = kivy.app.App.get_running_app()
        print 'button clicked', str(btn), str(image)
        image.source = app.resource_path('images/installing.png')
        print 'MainWidget ids:', self.view.ids
