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

class Model(object):
    """
    a simple model implementation to have a good seperation of data storage
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
        self.data[key] = value
