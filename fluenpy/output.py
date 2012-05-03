# coding: utf-8
"""
    fluenpy.output
    ~~~~~~~~~~~~~~

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""
from __future__ import print_function, division, absolute_import, with_statement
import logging
log = logging.getLogger(__name__)

from fluenpy.plugin import Plugin
from fluenpy.config import Configurable, config_param
from time import time as now
import gevent
import msgpack


class NullOutputChainClass(object):
    def next(self):
        pass
NullOutputChain = NullOutputChainClass()


class Output(Configurable):
    def start(self):
        pass

    def shutdown(self):
        pass

    def emit(self, tag, es, chain=NullOutputChain):
        pass

    def secondary_init(self, primary):
        if type(self) is not type(primary):
            log.warn("type of secondary output should be same as primary output:"
                     "primary=%r secondary=%r", type(primary), type(secondary),
                     )

class BufferedOutput(Output):

    _shutdown = False

    def __init__(self):
        super(BufferedOutput, self).__init__()
        self._last_retry_time = 0
        self._next_retry_time = 0
        self._secondary_limit = 8
        self._emit_count = 0

    buffer_type = config_param('string', 'memory')
    retry_limit = config_param('integer', 17)
    retry_wait = config_param('time', 1.0)

    def configure(self, conf):
        super(BufferedOutput, self).configure(conf)

        self._buffer = Plugin.new_buffer(self.buffer_type)
        self._buffer.configure(conf)
        #todo: secondary
        #todo: status

    def start(self):
        super(BufferedOutput, self).start()
        self._buffer.start()
        #todo: secondary.start()
        gevent.spawn(self.run)

    def run(self):
        while not self._shutdown:
            try:
                chunk = self._buffer.get(timeout=1.0)
            except gevent.queue.Empty:
                continue
            retry = 0
            retry_wait = self.retry_wait
            while retry <= self.retry_limit:
                try:
                    self.write(chunk)
                    break
                except Exception as e:
                    log.warn("fail to write: %r", e)
                    gevent.sleep(retry_wait)
                    retry_wait *= 2
        while 1:
            try:
                chunk = self._buffer.get_nowait()
                self.write(chunk.tag, chunk.read())
            except gevent.queue.Empty:
                break

    def shutdown(self):
        self._buffer.shutdown()
        self._shutdown = True
        super(BufferedOutput, self).shutdown()

    def emit(self, tag, es, chain=NullOutputChain, key=''):
        self._emit_count += 1
        data = self.format_stream(tag, es)
        self._buffer.emit(key, data, chain)

    def write(self, chunk):
        raise NotImplemented

    def format_stream(self, tag, es):
        out = bytearray()
        format = self.format
        for time, record in es:
            out += format(tag, time, record)
        return out


class ObjectBufferedOutput(BufferedOutput):
    u"""
    ``chunk`` に msgpack 形式でデータを格納する.
    継承したクラスは ``format`` メソッドを実装する必要がない.
    """

    def emit(self, tag, es, chain=NullOutputChain):
        self._emit_count += 1
        if callable(getattr(es, 'to_mpac', None)):
            data = es.to_mpac()
        else:
            data = b''.join(map(msgpack.packb, es))
        key = tag
        self._buffer.emit(key, data, chain)

