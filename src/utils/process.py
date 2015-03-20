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

"""
classes here in the module are taken from:
https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Multiprocessing
and corresponding thread
http://stackoverflow.com/questions/24944558/pyinstaller-built-windows-exe-fails-with-multiprocessing

They serve as workarounds, for windows issues regarding multiprocessing
"""

import multiprocessing.forking
import multiprocessing
import os
import sys
from multiprocessing.queues import SimpleQueue
from kivy.clock import Clock
import time

class _Popen(multiprocessing.forking.Popen):
    def __init__(self, *args, **kw):
        if hasattr(sys, 'frozen'):
            # We have to set original _MEIPASS2 value from sys._MEIPASS
            # to get --onefile mode working.
            os.putenv('_MEIPASS2', sys._MEIPASS)
        try:
            super(_Popen, self).__init__(*args, **kw)
        finally:
            if hasattr(sys, 'frozen'):
                # On some platforms (e.g. AIX) 'os.unsetenv()' is not
                # available. In those cases we cannot delete the variable
                # but only set it to the empty string. The bootloader
                # can handle this case.
                if hasattr(os, 'unsetenv'):
                    os.unsetenv('_MEIPASS2')
                else:
                    os.putenv('_MEIPASS2', '')

        # fix for request finding the certificates
        # see http://stackoverflow.com/questions/17158529/fixing-ssl-certificate-error-in-exe-compiled-with-py2exe-or-pyinstaller

class Process(multiprocessing.Process):
    _Popen = _Popen


# TODO: comment and treat failure and join process

class ParaQueue(SimpleQueue):
    def __init__(self, action_name):
        SimpleQueue.__init__(self)
        self.action_name = action_name

    def reject(self, data=None):
        msg = {'action': self.action_name, 'status': 'reject',
               'data': data}
        self.put(msg)

    def resolve(self, data=None):
        msg = {'action': self.action_name, 'status': 'resolve',
               'data': data}
        self.put(msg)

    def progress(self, data=None, percentage=0.0):
        msg = {'action': self.action_name, 'status': 'progress',
               'data': data, 'percentage': percentage}
        self.put(msg)

class Para(object):
    def __init__(self, func, args, target, action_name):
        super(Para, self).__init__()
        self.messagequeue = None
        self.func = func
        self.args = args
        self.target = target
        self.action_name = action_name
        self.current_child_process = None

    def _call_progress_handler(self, progress):
        funcname = 'on_' + progress['action'] + '_progress'
        func = getattr(self.target, funcname , None)
        if callable(func):
            func(progress['data'], progress['percentage'])

    def _call_resolve_handler(self, progress):
        funcname = 'on_' + progress['action'] + '_resolve'
        func = getattr(self.target, funcname , None)
        if callable(func):
            func(progress['data'])
        self._reset()

    def _call_reject_handler(self, progress):
        funcname = 'on_' + progress['action'] + '_reject'
        func = getattr(self.target, funcname , None)
        if callable(func):
            func(progress['data'])
        self._reset()

    def _reset(self):
        self.current_child_process.join()
        self.current_child_process = None
        Clock.unschedule(self.handle_messagequeue)

    def run(self):
        self.messagequeue = ParaQueue(self.action_name)
        p = Process(target=self.func, args=(self.messagequeue,) + self.args)
        p.start()
        self.current_child_process = p
        Clock.schedule_interval(self.handle_messagequeue, 1.0)

    def handle_messagequeue(self, dt):
        queue = self.messagequeue
        progress = None

        if queue and not queue.empty():
            progress = queue.get()

        if progress:
            if progress['status'] == 'progress':
                self._call_progress_handler(progress)

            elif progress['status'] == 'resolve':
                self._call_resolve_handler(progress)

            elif progress['status'] == 'reject':
                self._call_reject_handler(progress)

if __name__ == '__main__':

    def test_func(pq):
        pq.progress({'msg': 'test_func_has_started'})
        time.sleep(2)
        pq.progress({'msg': 'test_func in progress'})
        time.sleep(2)
        pq.resolve({'msg': 'test_func ready'})


    para = Para(test_func, (), None, 'testaction')
    para.run()
