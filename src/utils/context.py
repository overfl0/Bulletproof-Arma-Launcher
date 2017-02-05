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

import errno

from contextlib import contextmanager


@contextmanager
def ignore_exceptions(*exceptions):
    """Ignore exceptions raised inside the with block.

    Usage:
    with ignore_exceptions(KeyError):
        some_set.remove(key)
    """
    try:
        yield
    except exceptions:
        pass


@contextmanager
def ignore_nosuchfile_exception():
    """Ignore OSError.errno == errno.ENOENT exception raised inside the with block.

    Usage:
    with ignore_nosuchfile_exception():
        os.unlink(zip_path)
    """
    try:
        yield
    except OSError as ex:
        if ex.errno != errno.ENOENT:  # No such file or directory
            raise


@contextmanager
def ignore_nosuchfile_ioerror():
    """Ignore IOError.errno == errno.ENOENT exception raised inside the with block.

    Usage:
    with ignore_nosuchfile_exception():
        os.unlink(zip_path)
    """
    try:
        yield
    except IOError as ex:
        if ex.errno != errno.ENOENT:  # No such file or directory
            raise
