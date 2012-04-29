# coding: utf-8
"""
    fluenpy.output
    ~~~~~~~~~~~~~~

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""
from __future__ import print_function, division, absolute_import, with_statement
import logging

from fluenpy.plugin import Plugin
from fluenpy.config import Configurable, config_param

log = logging.getLogger(__name__)


class Output(Configurable):
    def start(self):
        pass

    def shutdown(self):
        pass

    def emit(self, tag, es, chain):
        pass

    def secondary_init(self, primary):
        if type(self) is not type(primary):
            log.warn("type of secondary output should be same as primary output:"
                     "primary=%r secondary=%r", type(primary), type(secondary),
                     )

class BufferedOutput(Output):
    def __init__(self):
        super(BufferedOutput, self).__init__()
        self._next_flush_time = 0
        self._last_retry_time = 0
        self._next_retry_time = 0
        self._secondary_limit = 8
        self._emit_count = 0

    buffer_type = config_param('string', 'memory')
    flush_interval = config_param('time', 60)
    retry_limit = config_param('integer', 17)
    retry_wait = config_param('time', 1.0)
    num_threads = config_param('integer', 1)

    def configure(self, conf):
        super(BufferedOutput, self).configure()

        self._buffer = Plugin.new_buffer(self.buffer_type)
        self._buffer.configure(conf)

        #todo: threads
        #todo: secondary
        #todo: status

    def start(self):
        self._next_flush_time = time.time() + self.flush_interval
        self._buffer.start()
        #todo: secondary.start()
        #todo: workers.start()

    def shutdown(self):
        self._buffer.shutdown()

    def emit(self, tag, es, chain, key=''):
        self._emit_count += 1
        data = self.format_stream(tag, es)
        self._buffer.emit(key, data, chain)

    def format_stream(self, tag, es):
        out = bytearray()
        format = self.format
        for time, record in es:
            out += format(tag, time, record)
        return out


class NullOutputChain(object):
    def next(self):
        pass

NullOutputChain.instance = NullOutputChain()
