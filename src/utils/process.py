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

from __future__ import unicode_literals

import multiprocessing.forking
import multiprocessing
import os
import sys
import io

from multiprocessing.queues import SimpleQueue
from multiprocessing import Lock, Pipe
from kivy.clock import Clock
from kivy.logger import Logger
from utils.testtools_compat import _format_exc_info
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


class ConnectionWrapper(object):
    def __init__(self, action_name, lock, con):
        super(ConnectionWrapper, self).__init__()
        self.action_name = action_name
        self.lock = lock
        self.con = con

    # the following methods have to be overwritten for the queue to work
    # under windows, since pickling is needed. Check link:
    # http://stackoverflow.com/questions/18906575/how-to-inherit-from-a-multiprocessing-queue
    def __getstate__(self):
        return self.action_name, self.lock, self.con

    def __setstate__(self, state):
        self.action_name, self.lock, self.con = state

    def reject(self, data=None):
        msg = {'action': self.action_name, 'status': 'reject',
               'data': data}
        self.con.send(msg)

    def resolve(self, data=None):
        msg = {'action': self.action_name, 'status': 'resolve',
               'data': data}
        self.con.send(msg)

    def progress(self, data=None, percentage=0.0):
        msg = {'action': self.action_name, 'status': 'progress',
               'data': data, 'percentage': percentage}

        # leave only one progress item on the queue at any time
        # self.lock.acquire()
        # if not self.empty():
        #     top = self.get()
        #
        #     if top['status'] != 'progress':
        #         self.put(top)
        self.con.send(msg)

class Para(object):
    def __init__(self, func, args, action_name):
        """
        constructor of the Para

        Args:
            func: a function which is called in another process
            args: the args which are passed to the function func contains
            action_name: identifier shich is used in the messagequeue. Actually
                         this is optional.

        Returns:
            The Para
        """
        super(Para, self).__init__()
        self.messagequeue = None
        self.func = func
        #self.protected_func = catchstacktrace(func)
        self.args = args
        self.action_name = action_name
        self.current_child_process = None
        self.progress_handler = []
        self.resolve_handler = []
        self.reject_handler = []
        self.state = 'pending' # pending, rejected or resolved
        self.lastdata = None # cached data from the last resolve or reject

    def add_progress_handler(self, func):
        """adds an progress handler which could be called multiple times

        Args:
            func: a function which gets called with two arguments
                data - dictionary which was passed on call of the progress function
                progress - number between 0 and 1 indicating the progress

        It gets called everytime the remote process calls the progress
        method on the messagequeue
        """
        self.progress_handler.append(func)

    def add_resolve_handler(self, func):
        """adds a handler which gets called once on resolve

        It gets called when the remote process calls the resolve
        method on the messagequeue
        """
        self.resolve_handler.append(func)

        if self.state == 'resolved':
            func(self.lastdata)

    def add_reject_handler(self, func):
        """adds a handler which gets called once on reject

        It gets called when the remote process calls the reject
        method on the messagequeue
        """
        self.reject_handler.append(func)

        if self.state == 'rejected':
            func(self.lastdata)

    def then(self, resolve_handler, reject_handler, progress_handler):
        """method registering all needed callback at once

        pass None to skip an arg
        """
        if resolve_handler:
            self.add_resolve_handler(resolve_handler)

        if reject_handler:
            self.add_reject_handler(reject_handler)

        if progress_handler:
            self.add_progress_handler(progress_handler)

    def _call_progress_handler(self, progress):
        for f in self.progress_handler:
            f(progress['data'], progress['percentage'])

    def _call_resolve_handler(self, progress):
        for f in self.resolve_handler:
            f(progress['data'])

        self.state = 'resolved'
        self._reset()

    def _call_reject_handler(self, progress):
        for f in self.reject_handler:
            f(progress['data'])

        self.state = 'rejected'
        self._reset()

    def _reset(self):
        #self.current_child_process.join()
        self.parent_conn.close()
        self.current_child_process = None
        Clock.unschedule(self.handle_messagequeue)
        Logger.debug('Para: {} joined process'.format(self))


    def run(self):
        self.lock = Lock()
        self.parent_conn, child_conn = Pipe()
        self.messagequeue = ConnectionWrapper(self.action_name, self.lock, child_conn)
        Logger.debug('Para: {} spwaning new process'.format(self))
        p = Process(target=self.func, args=(self.messagequeue,) + self.args)
        p.start()
        self.current_child_process = p
        Clock.schedule_interval(self.handle_messagequeue, 0.5)

    def handle_messagequeue(self, dt):
        con = self.parent_conn
        progress = None

        if con.poll():
            progress = con.recv()

        if progress:
            if progress['status'] == 'progress':
                self._call_progress_handler(progress)

            elif progress['status'] == 'resolve':
                self.lastdata = progress['data']
                # join process first
                self.current_child_process.join()
                self._call_resolve_handler(progress)

            elif progress['status'] == 'reject':
                self.lastdata = progress['data']
                # join process first
                self.current_child_process.join()
                self._call_reject_handler(progress)
        else:
            if not self.current_child_process.is_alive():
                message = '[{}] Child process terminated unexpectedly with code {}.'.format(
                    self.action_name, self.current_child_process.exitcode)
                self.lastdata = {'data': {'msg': message}}
                self._call_reject_handler(self.lastdata)

def catchstacktrace(func):
    def wrapper(con, *args, **kwargs):
        try:
            func(con, *args, **kwargs)
        except Exception:
            msg = "".join(_format_exc_info(*sys.exc_info()))
            con.reject({'exc': msg})

    return wrapper


class TestError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

if __name__ == '__main__':

    #
    # little test that the tracback of a childprocess gets catched
    #

    # def test_func(pq):
    #     print 'Process: ', os.getpid()
    #     try:
    #         pq.progress({'msg': 'test_func_has_started'})
    #         raise TestError('This exception got thrown for testing purposes')
    #     except Exception as e:
    #         msg = "".join(_format_exc_info(*sys.exc_info()))
    #         pq.reject({'exc': msg})

    @catchstacktrace
    def test_func(pq):
        pq.progress({'msg': 'test_func_has_started'})
        raise TestError('This exception got thrown for testing purposes')

    def on_reject(data):
        print 'para rejected, got data:'
        print data['exc']

    print 'Process: ', os.getpid()
    para = Para(test_func, (), 'testaction')
    para.then(None, on_reject, None)
    para.run()

    while not para.state == 'rejected':
        Clock.tick()

    print 'test good'
