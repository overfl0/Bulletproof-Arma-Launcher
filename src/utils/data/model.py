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

from kivy.event import EventDispatcher

# str variant of the unicode string on_change
# kivys api only works with non unicode strings
ON_CHANGE = 'on_change'.encode('ascii')


class Model(EventDispatcher):
    """
    a simple model implementation to have a good separation of data storage
    logic. Do not use this class directly. You should inherit from it

    Every child class has to specify a class variable called "fields". This
    should be an array of field names

    i.e.:
        fields: [
            {'name': 'use_exception_popup', 'defaultValue': True},
            {'name': 'launcher_basedir'}
        ]
    """

    fields = []

    def __init__(self):
        super(Model, self).__init__()

        self.register_event_type(ON_CHANGE)
        self.data = {}

        # init data fields
        for f in self.fields:
            self.data[f['name']] = f.get('defaultValue', None)

    def get(self, key):
        """
        get a data value from the model instance
        """
        return self.data[key]

    def set(self, key, value):
        """
        set data
        """
        old_value = self.data[key]
        if old_value != value:
            self.data[key] = value
            self.dispatch(ON_CHANGE, old_value, value)

        return self

    def on_change(self, *args):
        pass
