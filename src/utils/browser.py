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

import sys
import webbrowser


def open_hyperlink(url):
    """Open the url passed as argument.
    If the url points to a local file, encode it using the right encoding.
    """

    if url[1:].startswith(':\\'):  # C:\, D:\, etc...
        url = url.encode(sys.getfilesystemencoding())

    return webbrowser.open(url)
