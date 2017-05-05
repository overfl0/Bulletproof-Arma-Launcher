# Bulletproof Arma Launcher
# Copyright (C) 2016 Sascha Ebert
# Copyright (C) 2016 Lukasz Taczuk
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

import launcher_config
import sys

from kivy.base import ExceptionHandler
from kivy.base import ExceptionManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from utils import browser
from utils.primitive_git import get_git_sha1_auto
from utils.critical_messagebox import MessageBox
from utils.testtools_compat import _format_exc_info
from view.chainedpopup import ChainedPopup

DEFAULT_ERROR_MESSAGE = """Critical Error.
If you can't find an answer to your problem [color=3572b0][ref={}]on the troubleshooting page[/ref][/color]
copy the text below and post it on the bugtracker:

[color=3572b0][ref={}]{}[/ref][/color]
The error message has been copied to your clipboard. Press Ctrl+V to paste it.
""".format(launcher_config.troubleshooting_url, launcher_config.bugtracker_url, launcher_config.bugtracker_url)

POPUP_TITLE = """An error occurred"""
CRITICAL_POPUP_TITLE = """An error occurred. Copy it with Ctrl+C and submit a bug"""


def open_hyperlink(obj, ref):
    browser.open_hyperlink(ref)


class ErrorPopup(ChainedPopup):
    """Show a popup in case an error ocurred.
    Arguments:
    message - The message to be shown in a label.
    details - Shows an additional box containing details that may span dozens of lines.
    """
    def __init__(self, message=DEFAULT_ERROR_MESSAGE, details=None, label_markup=True,
                 auto_dismiss=False, **kwargs):
        kwargs.setdefault('size', (600, 500))
        kwargs.setdefault('title', POPUP_TITLE)

        bl = BoxLayout(orientation='vertical')
        la = Label(text=message, size_hint_y=0.3, markup=label_markup, halign='center')
        la.bind(on_ref_press=open_hyperlink)
        la.text_size = (550, None)  # Enable wrapping when text inside label is over 550px wide
        bl.add_widget(la)

        button = Button(text="Ok", size_hint=(None, None), height=40, width=150, pos_hint={'center_x': 0.5})
        button.bind(on_release=self.dismiss)

        if details:
            sv = ScrollView(size_hint=(1, 0.7),
                            bar_width=12,
                            scroll_type=['bars', 'content'],
                            bar_inactive_color=(0.5, 0.5, 0.5, 0.7)
                           )

            ti = TextInput(text=details, size_hint=(1, None))
            ti.copy(data=details)
            ti.bind(minimum_height=ti.setter('height'))
            sv.add_widget(ti)
            bl.add_widget(sv)

        if not auto_dismiss:
            bl.add_widget(button)

        super(ErrorPopup, self).__init__(
            content=bl, size_hint=(None, None), auto_dismiss=auto_dismiss, **kwargs
        )


def error_popup_decorator(func):
    def wrapper(*args, **kwargs):
        try:
            try:
                func(*args, **kwargs)

            except (UnicodeEncodeError, UnicodeDecodeError) as ex:
                error_message = "{}. Original exception: {} Text: {}".format(unicode(ex), type(ex).__name__, repr(ex.args[1]))
                raise UnicodeError, UnicodeError(error_message), sys.exc_info()[2]

        except Exception:
            build = get_git_sha1_auto()
            stacktrace = "".join(_format_exc_info(*sys.exc_info()))
            msg = 'Build: {}\n{}'.format(build, stacktrace)
            # p = ErrorPopup(details=msg)
            # p.open()
            MessageBox(msg, CRITICAL_POPUP_TITLE)

    return wrapper


class PopupHandler(ExceptionHandler):
    def handle_exception(self, inst):
        build = get_git_sha1_auto()
        stacktrace = "".join(_format_exc_info(*sys.exc_info()))
        msg = 'Build: {}\n{}'.format(build, stacktrace)
        p = ErrorPopup(details=msg)
        p.chain_open()
        return ExceptionManager.PASS
