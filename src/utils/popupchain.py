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

from __future__ import unicode_literals


class PopupChain(object):
    """A chain of ChainedPopup objects.
    After a ChainedPopup object has been appended to a PopupChain, try_open()
    has to be called to ensure the popup will be shown at some point in time.
    """

    def __init__(self):
        self.chain = []

    def append(self, popup):
        """Add the popup to the popup chain."""
        popup.bind(on_dismiss=lambda instance: self.open_next())
        self.chain.append(popup)

    def try_open(self):
        """Ensure the popup will be shown at some point in time.
        If there is no active popups, the popup will be shown now. If there are
        active popups, the popup will be shown as soon as previous popus will be
        closed.
        """

        # If there is more than one element in the chain, it means a popup is
        # already active.
        if len(self.chain) != 1:
            return

        self.chain[0].open()

    def open_next(self):
        """Callback the shows the first pending popup from the chain."""
        self.chain.pop(0)

        if len(self.chain):
            self.chain[0].open()

        # Return True to keep the current window open
