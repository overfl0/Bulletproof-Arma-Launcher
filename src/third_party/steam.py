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


def format_response(answers):
    return [answer if answer else '??/??' for answer in answers]

def format_response_final(answers):
    return [answer if answer else 'XX/XX' for answer in answers]

def query_server((server_id, server)):
    # Sleep to prevent flooding the network
    time.sleep(random.random() * 0.5)

    Logger.info('query_server: [{}] Querying server {} at {}:{}'.format(
        server_id, server.name, server.ip, int(server.port) + 1))

    address = (server.ip, int(server.port) + 1)

    try:
        server = valve.source.a2s.ServerQuerier(address, timeout=2)
        info = server.get_info()
        answer = '{}/{}'.format(info['player_count'], info['max_players'])

    except Exception as ex:  # valve.source.a2s.NoResponseError:
        Logger.error('query_server: [{}] Exception encountered: {}'.format(server_id, ex))
        Logger.error('query_server: [{}] Exception details: {}'.format(server_id, repr(ex)))

        return server_id, 'XX/XX'

    return server_id, answer


def query_servers(message_queue, servers):
    Logger.info('query_servers: Querying servers: {}'.format(servers))

    pool = ThreadPool(processes=10)
    pool_generator = pool.imap_unordered(query_server, enumerate(servers))
    answers = [None for _ in servers]

    # This is an overly complicated `for i in pool.imap_unordered`
    # That allows catching (and ignoring) exceptions in the workers
    while True:
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

    message_queue.resolve({'msg': 'Done', 'server_data': format_response_final(answers)})
    # message_queue.reject({'msg': 'Message!'})
