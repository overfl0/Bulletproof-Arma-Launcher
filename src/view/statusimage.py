from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.properties import StringProperty, BooleanProperty

class StatusImage(BoxLayout):
    """
    Class can be used to show images for loading indication
    """
    source = StringProperty('')
    hidden = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(StatusImage, self).__init__(**kwargs)
        self.image = None
        self.bind(source=self.on_source_set)
        self.bind(hidden=self.on_hidden_set)
        self._hidden = False

    def on_source_set(self, instance, source):
        if not self.image:
            self.image = Image(source=source, id='loading_image', anim_delay=0.05)
            self.add_widget(self.image)
        else:
            self.image.source = source

    def on_hidden_set(self, instance, hidden):
        if self._hidden == hidden:
            print 'doin nothing', hidden
            return

        if hidden == True:
            self.remove_widget(self.image)
            print 'hiding'
        else:
            self.add_widget(self.image)
            print 'showing'

        self._hidden = hidden

    def hide(self):
        pass

    def show(self):
        pass
