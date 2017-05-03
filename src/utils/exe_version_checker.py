# Bulletproof Arma Launcher
# Copyright (C) 2017 Lukasz Taczuk
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

import win32api

from collections import namedtuple


def get_version(path):
    """Get the executable version numbers
    Return a namedtuple with fields: ['major', 'minor', 'third', 'fourth']
    Return a None on error.
    """

    try:
        info = win32api.GetFileVersionInfo(path, "\\")
        ms = info['FileVersionMS']
        ls = info['FileVersionLS']
        version = (win32api.HIWORD(ms), win32api.LOWORD (ms), win32api.HIWORD (ls), win32api.LOWORD (ls))

        WinVersion = namedtuple('WinVersion', ['major', 'minor', 'third', 'fourth'])
        return WinVersion(*version)

    except Exception:
        # raise
        return None
