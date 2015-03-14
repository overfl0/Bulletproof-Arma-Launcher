

class UpdaterMainWidgetController(object):

    """docstring for UpdaterMainWidgetController"""
    def __init__(self, view):
        super(UpdaterMainWidgetController, self).__init__()
        self.view = view
        print 'init UpdaterMainWidgetController'


    def on_abort_button_release(self, button):
        print 'aborting', self.view.ids
        self.view.ids.status_label.text = 'Aborting ...'
