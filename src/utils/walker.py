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

import os
import platform


if platform.system() == 'Windows':
    import pywintypes
    import win32file

else:
    pass


def _get_file_id_windows(filename, is_directory):
    """Get the data that identifies a windows file.
    This is done by returning a tuple containing the drive serial unmber, and
    two file indexes.
    """

    try:
        hFile = win32file.CreateFile(filename, win32file.GENERIC_READ,
            win32file.FILE_SHARE_READ, None, win32file.OPEN_EXISTING,
            win32file.FILE_FLAG_BACKUP_SEMANTICS if is_directory else 0,
            None)

        try:
            _, _, _, _, dwVolumeSerialNumber, _, _, _, nFileIndexHigh, nFileIndexLow = \
                win32file.GetFileInformationByHandle (hFile)
            return dwVolumeSerialNumber, nFileIndexHigh, nFileIndexLow

        finally:
            hFile.Close()

    except pywintypes.error as ex:
        raise Exception(repr(ex))


def _get_file_id_unix(filename, is_directory):
    """Get the data that identifies a unix file.
    This is done by returning the inode number. Maybe returning a drive ID as
    well would be good.
    """

    # TODO: TEST THIS!!!
    # Especially how this behaves with symlinks
    # and with files on different drives that might get the same inode number
    return os.lstat(filename).st_ino


# Select the right function depending on the operating system
if platform.system() == 'Windows':
    _get_file_id = _get_file_id_windows

else:
    _get_file_id = _get_file_id_unix
    raise NotImplementedError('Linux support for the walking directories has not yet been tested!')


def walk(top, topdown=True, onerror=None, followlinks=False):
    """A junction aware walker that keeps traversed inodes and will NOT get into
    an infinite loop.
    """

    if topdown == False:
        raise Exception('You can\'t use topdown=False in this walker!')

    visited = set()

    for entry in os.walk(top, topdown, onerror, followlinks):
        try:
            file_id = _get_file_id(entry[0], True)

            if file_id in visited:
                # Already visited, skip it!
                del entry[1][:]  # Clear the directory so we don't descend into it
                continue

            visited.add(file_id)

        # At the risk of silencing important exceptions, we ignore potential
        # "don't have the right to open this file" problems
        except Exception:
            pass

        yield entry
