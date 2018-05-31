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

# TODO: Ensure correct handling of directory loops!

import os
import re
import string

from kivy.logger import Logger
from third_party.arma import Arma
from utils import walker
from utils.unicode_helpers import casefold
from sync.torrent_utils import path_can_be_a_mod, path_already_used_for_mod


def keep_meaningful_data(name):
    """Return the name after it has been changed to lowercase and stripped of
    all letters that are not latin characters or digits or '@'.
    This is done for a pseudo-fuzzy comparison where "@Kunduz, Afghanistan" and
    "@Kunduz Afghanistan" will match.
    """

    no_case = casefold(name)
    allowed_chars = string.letters + string.digits + '@'
    filtered_name = re.sub('[^{}]'.format(re.escape(allowed_chars)), '', no_case)

    return filtered_name


class CaseInsensitiveDict(dict):
    """http://stackoverflow.com/questions/2082152/case-insensitive-dictionary"""
    @classmethod
    def _k(cls, key):
        return keep_meaningful_data(key) if isinstance(key, basestring) else key

    def __init__(self, *args, **kwargs):
        super(CaseInsensitiveDict, self).__init__(*args, **kwargs)
        self._convert_keys()
    def __getitem__(self, key):
        return super(CaseInsensitiveDict, self).__getitem__(self.__class__._k(key))
    def __setitem__(self, key, value):
        super(CaseInsensitiveDict, self).__setitem__(self.__class__._k(key), value)
    def __delitem__(self, key):
        return super(CaseInsensitiveDict, self).__delitem__(self.__class__._k(key))
    def __contains__(self, key):
        return super(CaseInsensitiveDict, self).__contains__(self.__class__._k(key))
    def has_key(self, key):
        return super(CaseInsensitiveDict, self).has_key(self.__class__._k(key))
    def pop(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).pop(self.__class__._k(key), *args, **kwargs)
    def get(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).get(self.__class__._k(key), *args, **kwargs)
    def setdefault(self, key, *args, **kwargs):
        return super(CaseInsensitiveDict, self).setdefault(self.__class__._k(key), *args, **kwargs)
    def update(self, E={}, **F):
        super(CaseInsensitiveDict, self).update(self.__class__(E))
        super(CaseInsensitiveDict, self).update(self.__class__(**F))
    def _convert_keys(self):
        for k in list(self.keys()):
            v = super(CaseInsensitiveDict, self).pop(k)
            self.__setitem__(k, keep_meaningful_data(v))

# Hardcode this list for now. If it grows out of proportion, we'll see at making
# it configurable or downloadable by the launcher (maybe in metadata.json)
MOD_MAPPING = CaseInsensitiveDict({
    '@rhs_afrf3': '@RHSAFRF',
    '@rhs_usf3': '@RHSUSAF',
    '@EricJ_Taliban': '@TalibanFighters',  # Really?!?
    '@The_Unsung_Vietnam_War_mod': '@Unsung',
    '@FRL - Frontline': '@Frontline',
    '@FRL - Frontline IFA Compatibility': '@Frontline_compat_IFA',
    '@FRL - Frontline RHS Compatibility': '@Frontline_compat_RHS',
})


def get_mod_locations():
    """Return all the directories to search for existing mods."""
    mod_locations = []
    mod_locations.append(Arma.get_installation_path())

    return mod_locations


def find_mods(mods_directory, names, all_existing_mods, locations=None):
    """Find all the places where mods could already be stored on disk.
    For now this only does simple name matching and returns directories that
    have a name that matches the requested name. The search is case-insensitive.
    For efficiency reasons, all mods are searched for at the same time.

    Return a dictionary with <names> as keys and a list of proposed locations as
    values. Only mods with found locations are returned.

    Note: windows Junctions and Symlinks are treated as directories, even if
    they are broken. If broken, walker.walk(onerror=...) will be called.
    Otherwise, walker.walk will enter that directory.
    Note2: followlinks=False is IGNORED with windows Junctions and Symlinks!
    """



    filtered_names = set(keep_meaningful_data(name) for name in names)

    # inodes_visited = set()  # Store the inode of each directory to prevent infinite loops

    Logger.info('Finder: Searching for mods that have already been downloaded on disk: {}'.format(names))
    if locations is None:
        locations = get_mod_locations()

    response = {}

    for location in locations:
        Logger.info('Finder: Trying {}'.format(location))

        for root, _, _ in walker.walk(location, topdown=True, followlinks=True):

            filtered_base_root = keep_meaningful_data(os.path.basename(root))
            if filtered_base_root in filtered_names or filtered_base_root in MOD_MAPPING:
                # Find the right name in the right case
                for name in names:
                    meaningful_name = keep_meaningful_data(name)
                    if (meaningful_name == filtered_base_root or
                        MOD_MAPPING.get(filtered_base_root) == meaningful_name) and \
                       path_can_be_a_mod(root, mods_directory):
                        if not path_already_used_for_mod(root, all_existing_mods):
                            # response[name].append(root)
                            response.setdefault(name, []).append(root)
                            break

    Logger.info('Finder: probable mods locations: {}'.format(response))
    return response
