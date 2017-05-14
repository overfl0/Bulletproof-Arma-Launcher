# Bulletproof Arma Launcher
# Copyright (C) 2016 Sascha Ebert
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

"""
classes here in the module are taken from:
https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Multiprocessing
and corresponding thread
http://stackoverflow.com/questions/24944558/pyinstaller-built-windows-exe-fails-with-multiprocessing

They serve as workarounds, for windows issues regarding multiprocessing
"""

from __future__ import unicode_literals

import copy
import multiprocessing.forking
import multiprocessing
import os
import sys
import textwrap
import threading
import time

from multiprocessing.queues import SimpleQueue
from multiprocessing import Lock, Pipe
from kivy.clock import Clock
from kivy.logger import Logger
from utils.primitive_git import get_git_sha1_auto
from utils import system_processes
from utils.testtools_compat import _format_exc_info


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
    PING_MAX_TIMEOUT = 10
    PING_SEND_INTERVAL = 5

    def __init__(self, action_name, lock, con, use_threads):
        super(ConnectionWrapper, self).__init__()
        self.action_name = action_name
        self.lock = lock
        self.con = con
        self.broken_pipe = False
        self.received_ping_response = True
        self.ping_sent_at = time.time()
        self.use_threads = use_threads

    # the following methods have to be overwritten for the queue to work
    # under windows, since pickling is needed. Check link:
    # http://stackoverflow.com/questions/18906575/how-to-inherit-from-a-multiprocessing-queue
    def __getstate__(self):
        return (self.action_name,
               self.lock,
               self.con,
               self.broken_pipe,
               self.received_ping_response,  # Those two could be encapsulated into ping()
               self.ping_sent_at,  # Those two could be encapsulated into ping()
               self.use_threads,
               )

    def __setstate__(self, state):
        (self.action_name,
        self.lock,
        self.con,
        self.broken_pipe,
        self.received_ping_response,  # Those two could be encapsulated into ping()
        self.ping_sent_at,  # Those two could be encapsulated into ping()
        self.use_threads,
        ) = state

    def _send_message(self, msg):
        '''Send message through the pipe and note the pipe is broken on error.'''
        try:
            self.con.send(msg)
        except (EOFError, IOError):
            Logger.error('ConnectionWrapper: _send_message({}): Broken pipe! The remote process has probably terminated.'.format(self.action_name))
            self.broken_pipe = True

    def reject(self, data=None):
        msg = {'action': self.action_name, 'status': 'reject',
               'data': data}
        self._send_message(msg)

    def resolve(self, data=None):
        msg = {'action': self.action_name, 'status': 'resolve',
               'data': data}
        self._send_message(msg)

    def ping(self):
        """Ping the parent to ensure that he is still alive

        On lack of response, check the process for the presence of the parent.
        If the parent is not present, mark the pipe as broken.
        """

        # We don't need to ping because we're in the same thread as the "parent"
        if self.use_threads:
            return

        # TODO: Return if this is a thread
        if not self.received_ping_response and \
           self.ping_sent_at + self.PING_MAX_TIMEOUT < time.time():
            if not system_processes.is_parent_running(retval_on_error=True):
                Logger.error('ConnectionWrapper: receive_message: Broken pipe! The remote process has not answered the ping request.')
                self.broken_pipe = True
                Logger.debug('Ping timeout!')
                return

        if not self.received_ping_response or \
           self.ping_sent_at + self.PING_SEND_INTERVAL >= time.time():
            # Don't send the ping request yet
            return

        msg = {'action':self.action_name, 'status': '__ping__'}
        self._send_message(msg)
        Logger.debug('Sending ping!')
        self.ping_sent_at = time.time()
        self.received_ping_response = False


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
        self._send_message(msg)

    def receive_message(self):
        """Get the message passed to the process.
        Note the pipe is broken on error.
        Return a dictionary if a message was received
        Return None otherwise.
        """

        try:
            if not self.con.poll():
                # Note: disable pinging unless someone starts having problems
                # with parents dying.
                # self.ping()  # ping() takes care of not sending the ping msg too often
                return None

            message = self.con.recv()

            if message.get('command') == '__pong__':
                Logger.debug('Received pong!')
                self.received_ping_response = True
                return self.receive_message()

            return message

        except (EOFError, IOError):
            Logger.error('ConnectionWrapper: receive_message: Broken pipe! The remote process has probably terminated.')
            self.broken_pipe = True
            return None


class Para(object):

    JOIN_TIMEOUT_GRANULATION = 0.1
    HANDLE_MESSAGES_INTERVAL = 0.1

    def __init__(self, func, args, action_name, use_threads=False):
        """
        constructor of the Para

        Args:
            func: a function which is called in another process
            args: the args which are passed to the function func contains
            action_name: identifier which is used in the messagequeue. Actually
                         this is optional.

        Returns:
            The Para
        """
        super(Para, self).__init__()
        self.messagequeue = None
        self.func = func
        self.args = copy.deepcopy(args)
        self.action_name = action_name
        self.use_threads = use_threads
        self.current_child_process = None
        self.progress_handler = []
        self.resolve_handler = []
        self.reject_handler = []

        # the state of a para can be
        # pending, rejected or resolved or closingforreject and closingforresolve
        self.state = 'pending'
        self.lastdata = None  # cached data from the last resolve or reject
        self.lastprogress = None  # cached progress data from the last resolve or reject

    def is_open(self):
        """simple method which queries whenever the para is still in processing."""
        return not (self.state == 'resolved' or self.state == 'rejected')

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
        # self.current_child_process.join()
        self.parent_conn.close()
        self.current_child_process = None
        Clock.unschedule(self.handle_messagequeue)
        Logger.debug('Para: {} joined process'.format(self))

    def send_message(self, command, params=None):
        """Note: Feel free to refactor this message passing method"""
        msg = {'command': command}
        if params:
            msg['params'] = params

        self.parent_conn.send(msg)

    def request_termination(self):
        """sends a termination command to the child process"""
        self.send_message(command='terminate')

    def request_termination_and_break_promises(self):
        """Send a termination command to the child process. Additionally DON'T
        run any handlers at the end.
        Use this if you imperatively want to stop processing.
        """

        self.request_termination()
        self.progress_handler = []
        self.resolve_handler = []
        self.reject_handler = []

    def run(self):
        self.lock = Lock()
        self.parent_conn, child_conn = Pipe()
        self.messagequeue = ConnectionWrapper(self.action_name, self.lock, child_conn, use_threads=self.use_threads)
        Logger.debug('Para: {} spawning new {}'.format(self, 'thread' if self.use_threads else 'process'))

        if self.use_threads:
            p = threading.Thread(target=self.func, args=(self.messagequeue,) + self.args)
        else:
            p = Process(target=self.func, args=(self.messagequeue,) + self.args)

        p.start()
        self.current_child_process = p
        Clock.schedule_interval(self.handle_messagequeue, self.HANDLE_MESSAGES_INTERVAL)

    def handle_messagequeue(self, dt):
        con = self.parent_conn
        progress = None

        # handle closing phases first
        # try to join the child process
        if self.state == 'closingforreject':
            self.current_child_process.join(self.JOIN_TIMEOUT_GRANULATION)
            if not self.current_child_process.is_alive():
                self._call_reject_handler(self.lastprogress)

            return

        if self.state == 'closingforresolve':
            self.current_child_process.join(self.JOIN_TIMEOUT_GRANULATION)
            if not self.current_child_process.is_alive():
                self._call_resolve_handler(self.lastprogress)

            return

        if con.poll():
            progress = con.recv()

        if progress:
            if progress['status'] == 'progress':
                self._call_progress_handler(progress)

            elif progress['status'] == 'resolve':
                self.lastdata = progress['data']
                self.lastprogress = progress
                # enter closingphase cause a process can take long to
                # terminate
                self.state = 'closingforresolve'

            elif progress['status'] == 'reject':
                self.lastdata = progress['data']
                self.lastprogress = progress
                # enter closingphase cause a process can take long to
                # terminate
                self.state = 'closingforreject'

            elif progress['status'] == '__ping__':
                self.send_message('__pong__')
        else:
            if not self.current_child_process.is_alive():

                if hasattr(self.current_child_process, 'exitcode'):
                    # It's a Process
                    message = '[{}] Child process terminated unexpectedly with code {}.'.format(
                        self.action_name, self.current_child_process.exitcode)

                    # Special case (libtorrent crash)
                    if self.current_child_process.exitcode == -529697949 or \
                       self.current_child_process.exitcode == -1073741819:
                        message += '\n\n' + textwrap.dedent("""
                        This is probably a bug in Libtorrent that manifests itself
                        if there are more than 6 network interfaces enabled on the system.

                        To fix the issue, disable or remove unneeded interfaces until
                        you have 6 or less interfaces enabled.

                        Control Panel -> Network status and tasks -> Change adapter settings
                        Then, right-click and disable unneeded interfaces.
                        """)

                else:
                    # It's a Thread
                    message = '[{}] Child thread terminated unexpectedly.'.format(
                        self.action_name)

                self.lastdata = {'data': {'msg': message}}
                self._call_reject_handler(self.lastdata)

# TODO: Maybe make a decorator out of this
def _protected_call(messagequeue, function, action_name, *args, **kwargs):
    try:
        Logger.info('Para: Starting new thread/process for: {}'.format(action_name))
        return function(messagequeue, *args, **kwargs)
    except Exception:
        stacktrace = "".join(_format_exc_info(*sys.exc_info()))
        error = 'An error occurred in a subprocess:\nBuild: {}\n{}'.format(get_git_sha1_auto(), stacktrace).rstrip()
        messagequeue.reject({'details': error})

    finally:
        Logger.info('Para: Closing thread/process for: {}'.format(action_name))


def protected_para(func, args, action_name, then=None, use_threads=False):
    """Wrap a function with a catch-all try/except clause.
    On error a reject() is sent.
    """

    para = Para(_protected_call, (func, action_name) + args, action_name, use_threads=use_threads)

    # Optionally bind events before running the Para
    if then:
        para.then(*then)

    para.run()
    return para


