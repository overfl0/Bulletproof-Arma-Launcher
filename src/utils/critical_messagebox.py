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

import ctypes

# https://msdn.microsoft.com/en-us/library/windows/desktop/ms645505(v=vs.85).aspx
MB_ABORTRETRYIGNORE =     0x00000002
MB_CANCELTRYCONTINUE =    0x00000006
MB_HELP =                 0x00004000
MB_OK =                   0x00000000
MB_OKCANCEL =             0x00000001
MB_RETRYCANCEL =          0x00000005
MB_YESNO =                0x00000004
MB_YESNOCANCEL =          0x00000003

MB_ICONEXCLAMATION =      0x00000030
MB_ICONWARNING =          0x00000030
MB_ICONINFORMATION =      0x00000040
MB_ICONASTERISK =         0x00000040
MB_ICONQUESTION =         0x00000020
MB_ICONSTOP =             0x00000010
MB_ICONERROR =            0x00000010
MB_ICONHAND =             0x00000010

MB_DEFBUTTON1 =           0x00000000
MB_DEFBUTTON2 =           0x00000100
MB_DEFBUTTON3 =           0x00000200
MB_DEFBUTTON4 =           0x00000300

MB_APPLMODAL =            0x00000000
MB_SYSTEMMODAL =          0x00001000
MB_TASKMODAL =            0x00002000

MB_DEFAULT_DESKTOP_ONLY = 0x00020000
MB_RIGHT =                0x00080000
MB_RTLREADING =           0x00100000
MB_SETFOREGROUND =        0x00010000
MB_TOPMOST =              0x00040000
MB_SERVICE_NOTIFICATION = 0x00200000


def MessageBox(message, title, flags=MB_ICONEXCLAMATION):
    """The purpose of this message box is to give some information to the user when something
    goes so wrong that we cannot even be sure that kivy is running.
    """
    # Print to console if any present
    print repr(title)
    print repr(message)

    try:
        win32_msgbox = ctypes.windll.user32.MessageBoxW

        return win32_msgbox(None, message, title, flags)

    except AttributeError:  # Linux, no ctypes.windll present
        return None
