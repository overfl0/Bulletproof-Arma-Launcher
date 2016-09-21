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

# TODO: Implement this for linux as well

import pywintypes
import sys
import win32con
import win32event
import win32process

from utils import unicode_helpers
from win32com.shell import shellcon
from win32com.shell.shell import ShellExecuteEx


class AdminTask(object):
    def __init__(self, process):
        """Constructor. Pass the process handle as parameter."""

        self.process_handle = process['hProcess']
        self.returncode = None

    def wait(self):
        """Wait for the process to terminate.
        Return the process exit code.
        """

        return self.poll(timeout=win32event.INFINITE)

    def poll(self, timeout=0):
        """Check if the process has terminated.
        Return the process exit code if it has terminated or None otherwise.
        """

        obj = win32event.WaitForSingleObject(self.process_handle, timeout)
        if obj == win32event.WAIT_TIMEOUT:
            return None

        self.returncode = win32process.GetExitCodeProcess(self.process_handle)

        return self.returncode


def run_admin(executable, args):
    """Run executable as an administrator.
    Return an object that simulates a subset of subprocess.Popen class or None
    if the user chose to cancel elevating the executable rights.
    """

    params = ' '.join('"{}"'.format(arg) for arg in args)
    params = unicode_helpers.u_to_fs(params)

    if isinstance(executable, unicode):
        executable = unicode_helpers.u_to_fs(executable)

    try:
        process = ShellExecuteEx(nShow=win32con.SW_SHOWNORMAL,
                                 fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
                                 lpVerb='runas',
                                 lpFile=executable,
                                 lpParameters=params)

    except pywintypes.error as ex:
        if ex.winerror == 1223:
            return None  # The operation was canceled by the user.
        raise

    return AdminTask(process)

if __name__ == '__main__':
    import time

    executable = 'C:\\Program Files\\TeamSpeak 3 Client\\package_inst.exe'
    args = ['-silent', 'C:\\Users\\IEUser\\Documents\\Test\\@task_force_radio\\TeamSpeak 3 Client\\tfr.ts3_plugin']

    # With wait
    task = run_admin(executable, args)
    if not task:
        print "User cancelled the launch"
        sys.exit(1)

    retval = task.wait()
    print retval

    # With poll
    task = run_admin(executable, args)
    if not task:
        print "User cancelled the launch"
        sys.exit(1)

    while True:
        retval = task.poll()
        print retval

        if retval is not None:
            break

        time.sleep(0.3)
