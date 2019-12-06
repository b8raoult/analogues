#!/usr/bin/env python3


import uwsgi
import json

from analogues import maps


def application(env, sr):
    uwsgi.websocket_handshake(env['HTTP_SEC_WEBSOCKET_KEY'], env.get('HTTP_ORIGIN', ''))
    while True:
        data = json.loads(uwsgi.websocket_recv().decode('utf-8'))
        uwsgi.websocket_send_binary(maps.plot_from_data(data))
