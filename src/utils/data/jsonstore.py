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
import json

from kivy.logger import Logger

class JsonStore(object):
    """saves models to a json file"""
    def __init__(self, filepath):
        super(JsonStore, self).__init__()
        self.filepath = filepath

    def save(self, model):
        Logger.info('JsonStore: Saving model: {} to {} | {}'.format(
                model, self.filepath, model.data))

        string = json.dumps(model.data, sort_keys=True,
                indent=4, separators=(',', ': '))

        with open(self.filepath, "w") as text_file:
            text_file.write(string)

    def load(self, model, update=True):
        Logger.info('JsonStore: Loading model: {} from {} | {} '.format(
                model, self.filepath, model.data))

        with open(self.filepath, "r") as text_file:
            data = json.load(text_file)
            if update:
                model.data.update(data)
            else:
                model.data = data

        return model
