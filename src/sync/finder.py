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
from utils.unicode_helpers import casefold


def get_mod_locations():
    """Return all the directories to search for existing mods."""
    mod_locations = []
    mod_locations.append(Arma.get_installation_path())

    return mod_locations


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


def find_mods(names, locations=None):
    """Find all the places where mods could already be stored on disk.
    For now this only does simple name matching and returns directories that
    have a name that matches the requested name. The search is case-insensitive.
    For efficiency reasons, all mods are searched for at the same time.

    Return a dictionary with <names> as keys and a list of proposed locations as
    values. Only mods with found locations are returned.

    Note: windows Junctions and Symlinks are treated as directories, even if
    they are broken. If broken, os.walk(onerror=...) will be called.
    Otherwise, os.walk will enter that directory.
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

        for root, _, _ in os.walk(location, topdown=True, followlinks=True):

            # infinite loop protection
            """inode = os.lstat(root).st_ino  # Does not work on Windows!
            print inode
            if inode in inodes_visited:
                Logger.info('Finder: directory already searched: {}'.format(root))

                del dirs[:]  # Don't descend deeper
                continue

            inodes_visited.add(inode)"""

            filtered_base_root = keep_meaningful_data(os.path.basename(root))
            if filtered_base_root in filtered_names:
                # Find the right name in the right case
                for name in names:
                    if keep_meaningful_data(name) == filtered_base_root:
                        # response[name].append(root)
                        response.setdefault(name, []).append(root)
                        break

    Logger.info('Finder: probable mods locations: {}'.format(response))
    return response
