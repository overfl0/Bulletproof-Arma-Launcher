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

import valve.source.a2s

from kivy.logger import Logger

def format_response(answers):
    return [answer if answer else '??/??' for answer in answers]

def format_response_final(answers):
    return [answer if answer else 'XX/XX' for answer in answers]

def query_servers(message_queue, servers):
    Logger.info('query_servers: Querying servers: {}'.format(servers))

    answers = [None for _ in servers]

    # message_queue.progress({'msg': 'progress'}, 0)
    # message_queue.reject({'msg': 'Message!'})

    for i, server in enumerate(servers):
        Logger.info('query_servers: Querying server {} at{}:{}'.format(
            server.name, server.ip, int(server.port) + 1))

        address = (server.ip, int(server.port) + 1)

        try:
            server = valve.source.a2s.ServerQuerier(address)
            info = server.get_info()

        except Exception as ex:  # valve.source.a2s.NoResponseError:
            Logger.error('query_servers: Exception encountered: {}'.format(ex))
            Logger.error('query_servers: Exception details: {}'.format(repr(ex)))
            continue

        Logger.info('query_servers: Players: {} / {}'.format(info['player_count'], info['max_players']))
        answers[i] = '{}/{}'.format(info['player_count'], info['max_players'])
        message_queue.progress({'msg': 'progress', 'server_data': format_response(answers)}, 0)

    message_queue.resolve({'msg': 'Done', 'server_data': format_response_final(answers)})
