# coding: utf-8
"""
    fluenpy.plugins.out_forward
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""

from __future__ import print_function, division, absolute_import, with_statement
import logging
log = logging.getLogger(__name__)

from fluenpy import error
from fluenpy.output import ObjectBufferedOutput
from fluenpy.plugin import Plugin
from fluenpy.config import config_param
import gevent.socket as socket
import msgpack
import struct


DEFAULT_LISTEN_PORT = 24224


class ForwardOutput(ObjectBufferedOutput):

    def __init__(self):
        super(ForwardOutput, self).__init__()
        self._nodes = []

    def configure(self, conf):
        super(ForwardOutput, self).configure(conf)

        for e in conf.elements:
            if e.name != "server":
                continue
            host = e['host']
            port = int(e.get('port', DEFAULT_LISTEN_PORT))
            self._nodes.append((host, port))
            log.info("adding forwarding server %s:%s", host, port)

    def write(self, chunk):
        key = chunk.key
        data = chunk.read()
        log.debug("sending tag=%s data=%dbytes", key, len(data))
        for node in self._nodes:
            try:
                self.send_data(node, key, data)
                break
            except Exception as e:
                log.warn("fail to send data to %s: %s", node, e)
                pass
        else:
            raise Exception("No nodes are available.")

    def send_data(self, node, tag, data):
        sock = socket.socket()
        header = b"\x92" + msgpack.packb(tag) + b"\xdb" + struct.pack("!L", len(data))
        sock.connect(node)
        try:
            sock.sendall(header)
            sock.sendall(data)
        finally:
            sock.close()

Plugin.register_output('forward', ForwardOutput)
