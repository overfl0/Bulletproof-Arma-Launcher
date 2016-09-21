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

import json
import os

from kivy.logger import Logger
from utils.paths import mkdir_p


class JsonStore(object):
    """saves models to a json file"""
    def __init__(self, filepath):
        super(JsonStore, self).__init__()
        self.filepath = filepath

    def _save_to_file(self, filename, contents):
        """Save to file while ensuring the directory is created."""
        directories = os.path.dirname(filename)

        if directories and not os.path.isdir(directories):
            mkdir_p(directories)

        with open(filename, "w") as text_file:
            text_file.write(contents)

    def save(self, model):


        # build new dict with items which have persist set not to False
        dict_to_save = {}

        for field in model.fields:
            if 'persist' in field and field['persist'] == False:
                continue
            else:
                dict_to_save[field['name']] = model.get(field['name'])


        string = json.dumps(dict_to_save, sort_keys=True,
                            indent=4, separators=(',', ': '))

        Logger.info('JsonStore: Saving model: {} to {} | {}'.format(
                    model, self.filepath, string))

        self._save_to_file(self.filepath, string)

    def load(self, model, update=True):

        with open(self.filepath, "r") as text_file:
            data = json.load(text_file)
            if update:
                model.data.update(data)
            else:
                model.data = data

        nice_model_data = json.dumps(model.data, sort_keys=True,
                            indent=4, separators=(',', ': '))

        Logger.info('JsonStore: Loaded model: {} from {} | {} '.format(
                    model, self.filepath, nice_model_data))

        return model
