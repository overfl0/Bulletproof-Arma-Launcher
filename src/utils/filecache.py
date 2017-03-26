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

import errno
import hashlib
import os

from utils import paths
from utils import context


def get_cache_directory():
    return paths.get_launcher_directory('filecache')


def map_file(url):
    """Get the path where the file should be stored in the cache."""

    file_name = hashlib.sha256(url).hexdigest()
    return os.path.join(get_cache_directory(), file_name)


def get_file(url):
    """Get the file contents from the cache or None if the file is not present
    in the cache.
    """

    path = map_file(url)
    f = None

    try:
        f = open(path, 'rb')
        return f.read()

    except IOError as ex:
        if ex.errno == errno.ENOENT:  # No such file
            return None

        raise

    finally:
        if f:
            f.close()


def save_file(url, data):
    """Save the file contents to the cache.
    The contents of the file are saved to a temporary file and then moved to
    ensure that no truncated file is present in the cache.
    """

    # Ensure the directory exists
    paths.mkdir_p(get_cache_directory())

    path = map_file(url)
    tmp_path = path + '_tmp'

    f = open(tmp_path, 'wb')
    f.write(data)
    f.close()

    # Ensure the file does not exist (would raise an exception on Windows
    with context.ignore_nosuchfile_exception():
        os.unlink(path)

    os.rename(tmp_path, path)
