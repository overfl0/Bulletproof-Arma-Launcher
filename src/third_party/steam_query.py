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

import random
import time
import valve.source.a2s

from kivy.logger import Logger
from multiprocessing.pool import ThreadPool


RESPONSE_UNKNOWN = '?/?'
RESPONSE_DOWN = '-/-'

CONNECTIONS_ATTEMPTS = 3
CONNECTION_TIMEOUT = 2
MAX_SLEEP_TIMEOUT = 0.5
POOL_PROCESSES = 10


def format_response(answers):
    """Return responses while the checking is still running."""
    return [answer if answer else RESPONSE_UNKNOWN for answer in answers]


def format_response_final(answers):
    """Return the final responses when it is clear that some servers are down."""
    return [answer if answer != RESPONSE_UNKNOWN else RESPONSE_DOWN for answer in answers]


def query_server((server_id, server)):
    """Query a server for its player count.
    This function is run in a separate thread.
    """

    # Sleep to prevent flooding the network
    time.sleep(random.random() * MAX_SLEEP_TIMEOUT)

    Logger.info('query_server: [{}] Querying server {} at {}:{}'.format(
        server_id, server.name, server.ip, int(server.port) + 1))

    address = (server.ip, int(server.port) + 1)

    try:
        server = valve.source.a2s.ServerQuerier(address, timeout=CONNECTION_TIMEOUT)
        info = server.get_info()
        answer = '{}/{}'.format(info['player_count'], info['max_players'])

    except Exception as ex:  # valve.source.a2s.NoResponseError:
        Logger.error('query_server: [{}] Exception encountered: {}'.format(server_id, ex))
        Logger.error('query_server: [{}] Exception details: {}'.format(server_id, repr(ex)))

        return server_id, RESPONSE_UNKNOWN

    return server_id, answer

# TODO: Move all of this into a class
force_termination = False
def handle_messages(message_queue):
    """Handle all incoming messages passed from the main process.
    For now, the amount of commands is too small to implement a fully
    fledged message handling mechanism with callbacks and decorators.
    A simple if/elif will do.
    """

    global force_termination

    # We are canceling the downloads
    message = message_queue.receive_message()
    if not message:
        return

    command = message.get('command')
    # params = message.get('params')

    if command == 'terminate':
        Logger.info('query_servers wants termination')
        force_termination = True


def query_servers(message_queue, servers):
    global force_termination

    force_termination = False
    Logger.info('query_servers: Querying servers: {}'.format(servers))

    answers = [RESPONSE_UNKNOWN for _ in servers]
    pool = ThreadPool(processes=POOL_PROCESSES)

    message_queue.progress({'msg': 'progress', 'server_data': format_response(answers)}, 0)

    # Check the failed servers 3 times
    for iteration in range(CONNECTIONS_ATTEMPTS):
        # Get all the servers that have not yet responded
        servers_to_check = [(i, server) for i, server in enumerate(servers) if answers[i] == RESPONSE_UNKNOWN]

        if servers_to_check and iteration > 0:
            # Wait a bit in case the network was the culprit of previous failures
            time.sleep(MAX_SLEEP_TIMEOUT)

        pool_generator = pool.imap_unordered(query_server, servers_to_check)

        # This is an overly complicated `for i in pool.imap_unordered`
        # That allows catching (and ignoring) exceptions in the workers
        while True:
            handle_messages(message_queue)
            if force_termination:
                Logger.info('query_servers: Received termination request. Stopping...')
                break

            try:
                server_id, response = pool_generator.next()

            except StopIteration:
                break

            except Exception:
                raise
                # print "Got Exception: {}, continuing...".format(type(ex))
                # continue

            Logger.info('query_servers: Players: {}'.format(response))
            answers[server_id] = response
            message_queue.progress({'msg': 'progress', 'server_data': format_response(answers)}, 0)

        if force_termination:
            Logger.info('query_servers: Received termination request. Stopping... (2)')
            break

    message_queue.resolve({'msg': 'Done', 'server_data': format_response_final(answers)})

    pool.close()
    pool.join()
