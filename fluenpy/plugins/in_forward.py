# coding: utf-8
"""
    fluenpy.plugins.in_forward
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""
from __future__ import print_function, division, absolute_import, with_statement
import logging
log = logging.getLogger(__name__)

import os
from time import time as now

from fluenpy.engine import Engine
from fluenpy.plugin import Plugin
from fluenpy.input import Input
from fluenpy.config import config_param
from gevent.server import DatagramServer, StreamServer

try:
    import simplejson as json
except ImportError:
    import json

from msgpack import Unpacker


class UnpackStream(object):
    def __init__(self, bytes):
        self._bytes = bytes

    def __iter__(self):
        unp = Unpacker()
        unp.feed(self._bytes)
        return unp

    def to_mpac(self):
        return self._bytes

class HeartbeatServer(DatagramServer):
    def handle(self, data, address):
        self.socket.sendto('', address)

class ForwardInput(Input):

    port = config_param('integer', 9880)
    bind = config_param('string', '0.0.0.0')

    def start(self):
        log.info("start forward server on %s:%s", self.bind, self.port)
        self._server = StreamServer((self.bind, self.port), self.on_connect)
        self._server.start()
        self._hbserver = HeartbeatServer((self.bind, self.port))
        self._hbserver.start()

    def shutdown(self):
        self._hbserver.stop()
        self._server.stop()

    def on_message(self, msg):
        tag = msg[0]
        log.debug("on_message: recieved message %s", tag)
        entries = msg[1]
        ent_type = type(entries)

        if ent_type is bytes:
            Engine.emit_stream(tag, UnpackStream(entries))
        elif ent_type in (list, tuple):
            Engine.emit_stream(
                    tag,
                    [(e[0] or now(), e[1]) for e in entries],
                    )
        else:
            Engine.emit(tag, msg[1] or now(), msg[2])


    def json_handler(self, data, sock):
        decode = json.JSONDecoder().raw_decode
        pos = 0
        while 1:
            try:
                obj, pos = decode(data, pos)
                self.on_message(obj)
            except (ValueError, StopIteration):
                data = data[pos:]
                next_data = sock.recv(128*1024)
                if not next_data:
                    break
                data += next_data
                pos = 0

    def mpack_handler(self, data, sock):
        unpacker = Unpacker()
        unpacker.feed(data)
        # default chunk size of memory buffer is 32MB
        RECV_SIZE = 32*1024*1024
        while 1:
            for msg in unpacker:
                self.on_message(msg)
            next_data = sock.recv(RECV_SIZE)
            if not next_data:
                break
            unpacker.feed(next_data)

    def on_connect(self, sock, addr):
        try:
            data = sock.recv(128*1024)
            if not data:
                return
            if data[0] in b'{[':
                self.json_handler(data, sock)
            else:
                self.mpack_handler(data, sock)
        finally:
            sock.close()

Plugin.register_input('forward', ForwardInput)
