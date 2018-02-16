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

import socket
import textwrap
import time

from kivy.logger import Logger
from utils.critical_messagebox import MessageBox

# from kivy.config import Config
# Config.set('kivy', 'log_level', 'debug')

class ClientQueryException(Exception):
    def __init__(self, message, errno, command):
        readable = 'Teamspeak command: \'{}\' returned error {}: {}'.format(
            command, errno, message)

        super(ClientQueryException, self).__init__(readable)

        try:
            self.errno = int(errno)
        except:
            self.errno = -1

        self.command = command
        self.msg = message


class ClientQuery(object):

    def __init__(self, *args, **kwargs):
        super(ClientQuery, self).__init__(*args, **kwargs)

        self.socket = None

    def connect(self, host=None, port=None):
        """Connect to the server and set the socket timeouts.

        Return self to allow for method chaining."""

        host = host if host else '127.0.0.1'
        port = port if port is not None else 25639

        try:
            Logger.info('ClientQuery: Trying to connect to: {}'.format(host, port))
            self.socket = socket.create_connection((host, port), timeout=5)

        except socket.timeout:
            Logger.error('ClientQuery: Connection refused! (timeout)')
            return None

        except socket.error as ex:
            if ex.errno == 10061:
                Logger.error('ClientQuery: Connection refused!')
                return None

            # socket.error: [Errno 10053] An established connection was aborted by the software in your host machine

            raise

        Logger.debug('ClientQuery: Connected successfully!')
        self.socket.settimeout(2)
        return self

    def _send(self, command):
        """Send a command to the TS server.
        Set the socket to None on timeout.
        """

        if not self.socket:
            return

        try:
            self.socket.send(command + '\n')
        except socket.error as ex:
            if type(ex) == socket.timeout:
                Logger.error('ClientQuery: send: got a timeout. Closing the socket.')
                self.socket = None
                return None

            raise

    def _recv(self):
        """Retrieve the response from the server.
        Will call the underlying recv method from the socket as long as it
        doesn't find an error code signifying an end of the message or until
        it times out.

        On timeout, set the socket to None.
        """

        if not self.socket:
            return None

        time_start = time.time()

        data = ''
        while True:
            if time.time() - time_start > self.socket.gettimeout():
                Logger.error('ClientQuery: recv: got a cumulative timeout. Closing the socket.')
                self.socket = None
                return None

            try:
                retval = self.socket.recv(2 ** 14)

            except socket.error as ex:
                if type(ex) == socket.timeout:
                    Logger.error('ClientQuery: recv: got a timeout. Closing the socket.')
                    self.socket = None
                    return None

                raise

            data += retval

            lines = data.split('\n\r')
            Logger.debug('ClientQuery: cumulative recv: {}'.format(lines))

            for line in lines[:-1]:  # to prevent skipping receiving the last '' line
                if line.startswith('error '):
                    return lines

            # Workaround for the first message after connecting
            if lines[0] == 'TS3 Client' and \
               lines[-2].startswith('selected schandlerid='):
                return lines

    def init(self, api_key=None):
        """Perform a set of actions to initialize the TS connection so that
        further commands can be executed on that connection.

        Returns self to allow for method chaining.
        """

        connect_ok = self.connect()

        if not connect_ok:
            return None

        self._recv()

        if self.auth_call_present():
            if api_key:
                self.authenticate(api_key)

            else:
                message = textwrap.dedent('''
                    Teamspeak clientquery requires api_key but it it could not  be found on disk!
                    The Teamspeak server detection will not work correctly!
                ''')
                MessageBox(message, 'Teamspeak detection error!')

        return self

    def get_value(self, tokens, name, multi=False):
        """Get the value of a token from a list of those tokens.
        The format is "key=value".
        If multi == True, returns a list of values of all the tokens which keys
        match the given name.

        If the key is not found, returns None if multi is False or an empty
        array otherwise.
        """

        # Default return value
        retval = [] if multi else None

        for token in tokens:
            try:
                key, val = token.split('=')

            except ValueError:  # Cannot unpack
                continue

            if key == name:
                if multi:
                    retval.append(val)
                else:
                    return val

        return retval

    def parse_error(self, lines):
        """Parse the given lines in search of a Teamspeak Client Query error
        code. If no error code is found within those lines, raise an exception.

        Return None if no error.
        Return (errno, error_message) on error.
        """

        for line in lines[::-1]:
            if line.startswith('error '):
                break
        else:
            raise ClientQueryException('No error code in response from Teamspeak', '-1', '<unknown>')

        tokens = line.split()
        id_ = self.get_value(tokens[1:], 'id')
        msg = self.get_value(tokens[1:], 'msg')

        if not msg:
            msg = ''

        if id_ and int(id_) == 0:
            return None

        msg = msg.replace('\s', ' ')
        Logger.error('ClientQuery: id: {}, message: {}'.format(id_, msg))

        return (id_, msg)

    def run_command(self, cmd):
        """Execute a Client Query command and return the full response."""

        self._send(cmd)
        lines = self._recv()

        if lines is None:
            raise ClientQueryException('Connection closed by Teamspeak client!', '-2', cmd)

        error = self.parse_error(lines)
        if error is None:
            return lines

        raise ClientQueryException(message=error[1], errno=error[0], command=cmd)

    # Higher level commands

    def authenticate(self, api_key):
        response = self.run_command('auth apikey={}'.format(api_key))

    def auth_call_present(self):
        """Check if the `auth` call is present in Teamspeak.
        This is done by trying to call the `help auth` call. If it succeeds, it
        means the call is present and you have to authenticate before performing
        any serious actions.
        """

        try:
            self.run_command('help auth')

        except ClientQueryException as ex:
            if ex.errno == 1538:
                return False  # Invalid parameter - command auth is not present

            raise

        return True

    def get_server_tokens(self, handler_id):
        """Retrieve the IDs of all the server handlers used by Teamspeak.
        Note that not all handlers are actually connected and will return an
        error when asked for connection details. This has to be checked later!
        """

        response = self.run_command('use {}'.format(handler_id))

        response = self.run_command('serverconnectinfo')
        tokens = response[0].split(' ')

        return tokens

    def get_servers_connected(self):
        """Get the addresses (IP or domain string) of all the servers the
        Teamspeak client is currently connected to.
        """

        response = self.run_command('serverconnectionhandlerlist')
        tokens = response[0]

        server_handlers = self.get_value(tokens.split('|'), 'schandlerid', multi=True)
        Logger.debug('ClientQuery: got server handlers: {}'.format(server_handlers))
        server_handlers_int = [int(sh) for sh in server_handlers]

        ips = []

        for handler in server_handlers_int:
            try:
                tokens = self.get_server_tokens(handler)
                ip = self.get_value(tokens, 'ip')
                ips.append(ip)

            except ClientQueryException as ex:
                if ex.errno == 1794:
                    continue  # Not connected on this handler

                raise

        return ips


def get_TS_servers_connected(api_key):
    """Get the addresses (IP or domain string) of all the servers the
    Teamspeak client is currently connected to.
    """

    try:
        ts = ClientQuery().init(api_key=api_key)

        if not ts:
            return []

        return ts.get_servers_connected()

    # Hotfix for #216 (TeamSpeak changed the ClientQuery to use an API key)
    except ClientQueryException as ex:
        Logger.error('ClientQuery: {}'.format(ex))
        import traceback
        Logger.error('ClientQuery: {}'.format(traceback.format_exc()))

        return []


if __name__ == '__main__':
    print get_TS_servers_connected()
