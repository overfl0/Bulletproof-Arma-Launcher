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

import os.path
import thread
import sys
import webbrowser

from utils.critical_messagebox import MessageBox

# from utils.process import Process


def _open_hyperlink(url):
    """Open the url passed as argument.
    If the url points to a local file, encode it using the right encoding.
    """

    if url[1:].startswith(':\\'):  # C:\, D:\, etc...
        if not os.path.exists(url):
            MessageBox('The file or directory does not exist',
                       'Can\'t open file or directory')
            return

        url = url.encode(sys.getfilesystemencoding())

    return webbrowser.open(url)


def open_hyperlink(url):
    """Open the url passed as argument.
    If the url points to a local file, encode it using the right encoding.
    Calls another process to ensure it terminates right away and does not block
    the main process/thread.
    """
    # p = Process(target=_open_hyperlink, args=[url])
    # p.start()
    # Honestly, I don't know if using either threads or processes changes anything.
    # Both seem to freeze the UI at some point.
    # thread.start_new_thread(_open_hyperlink, (url,))
    _open_hyperlink(url)
