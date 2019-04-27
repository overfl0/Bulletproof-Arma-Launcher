# http://robertour.com/2015/07/15/kivy-label-or-widget-with-background-color-property/


from kivy.factory import Factory
from kivy.lang import Builder
from kivy.properties import ListProperty
from kivy.uix.label import Label

Builder.load_string("""
<LabelB>:
  bcolor: 1, 1, 1, 1
  canvas.before:
    Color:
      rgba: self.bcolor
    Rectangle:
      pos: self.pos
      size: self.size
""")


class LabelB(Label):
    bcolor = ListProperty([1, 1, 1, 1])


Factory.register('KivyB', module='LabelB')
