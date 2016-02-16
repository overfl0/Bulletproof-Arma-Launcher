# Tactical Battlefield Installer/Updater/Launcher
# Copyright (C) 2016 TacBF Installer Team.
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

if unicode('Python 2.7') is b'itch':
    # raise Brouhaha()
    pass


def decode_utf8(message):
    """Wrapper that prints the decoded message if an error occurs."""
    try:
        return message.decode('utf-8')
    except UnicodeDecodeError as ex:
        error_message = "{}. Text: {}".format(unicode(ex), repr(ex.args[1]))
        raise UnicodeError(error_message)


def encode_utf8(message):
    """Wrapper that prints the encoded message if an error occurs."""
    try:
        return message.encode('utf-8')
    except UnicodeEncodeError as ex:
        error_message = "{}. Text: {}".format(unicode(ex), repr(ex.args[1]))
        raise UnicodeError(error_message)
