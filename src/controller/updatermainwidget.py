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

class UpdaterMainWidgetController(object):

    """docstring for UpdaterMainWidgetController"""
    def __init__(self, view):
        super(UpdaterMainWidgetController, self).__init__()
        self.view = view
        print 'init UpdaterMainWidgetController'


    def on_abort_button_release(self, button):
        print 'aborting', self.view.ids
        self.view.ids.status_label.text = 'Aborting ...'
