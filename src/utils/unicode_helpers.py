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

import sys

if unicode('Python 2.7') is b'itch':
    # raise Brouhaha()
    pass


def decode_utf8(message, errors='strict'):
    """Wrapper that prints the decoded message if an error occurs."""
    try:
        return message.decode('utf-8', errors=errors)
    except UnicodeDecodeError as ex:
        error_message = "{}. Original exception: {} Text: {}".format(unicode(ex), type(ex).__name__, repr(ex.args[1]))
        raise UnicodeError, UnicodeError(error_message), sys.exc_info()[2]


def encode_utf8(message, errors='strict'):
    """Wrapper that prints the encoded message if an error occurs."""
    try:
        return message.encode('utf-8', errors=errors)
    except UnicodeEncodeError as ex:
        error_message = "{}. Original exception: {} Text: {}".format(unicode(ex), type(ex).__name__, repr(ex.args[1]))
        raise UnicodeError, UnicodeError(error_message), sys.exc_info()[2]


def u_to_fs(unicode_string):
    """Convert an unicode string to the file system encoding"""
    return unicode_string.encode(sys.getfilesystemencoding())


def fs_to_u(fs_string):
    """Convert a string from the file system encoding to unicode"""
    return fs_string.decode(sys.getfilesystemencoding())


def u_to_fs_list(args):
    """Convert a list of arguments from unicode to the file system encoding"""
    return [u_to_fs(arg) for arg in args]


def fs_to_u_list(args):
    """Convert a list of arguments from the file system encoding to unicode"""
    return [fs_to_u(arg) for arg in args]


def casefold(s):
    """Return a version of the string for caseless matching."""
    return s.upper().lower()
