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

from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout

LABEL_TEXT = """This is alpha Software and may destroy your computer ... and
your house. Do not trust german developers"""

ST_DEFAULT = """No stacktrace given!"""

POPUP_TITLE = """Alpha Software Agreement"""

class AlphaNotification(Popup):
    def __init__(self):
        bl = BoxLayout(orientation='vertical')
        la = Label(text=LABEL_TEXT, size_hint_y=0.8)
        button = Button(text="Ok", size_hint_y=0.2)
        button.bind(on_release=self.dismiss)

        bl.add_widget(la)
        bl.add_widget(button)

        super(AlphaNotification, self).__init__(title=POPUP_TITLE,
            content=bl, size_hint=(None, None), size=(600, 400))
