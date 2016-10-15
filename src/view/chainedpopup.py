# Bulletproof Arma Launcher
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

import kivy.app

from vresizablepopup import VResizablePopup


class ChainedPopup(VResizablePopup):
    """Popup that is shown only when previous popups have disappeared.
    They can be chained by calling the chain_open() method instead of open().

    You should NOT mix chain_open() calls with open() calls.
    Nothing will explode but the latest of these two windows will end on top.
    """

    def __init__(self, *args, **kwargs):
        super(ChainedPopup, self).__init__(*args, **kwargs)

    def chain_open(self):
        '''Open this message box as soon as the previous box has been closed.'''
        popup_chain = kivy.app.App.get_running_app().popup_chain
        popup_chain.append(self)
        popup_chain.try_open()
