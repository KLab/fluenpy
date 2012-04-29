# coding: utf-8
"""
    fluenpy.buffer
    ~~~~~~~~~~~~~~

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""
from __future__ import print_function, division, absolute_import, with_statement
import logging
log = logging.getLogger(__name__)

from fluenpy import error
from fluenpy.config import Configurable, config_param

from collections import defaultdict
import gevent.queue as gqueue
import gevent


class BaseBufferChunk(object):
    def __init__(self, key):
        self.key = key

    def __iadd__(self, data):
        """Append *data* to this chunk."""
        raise NotImplemented

    def __len__(self):
        """Return bytesize of this chunk."""
        raise NotImplemented


class BaseBuffer(Configurable):

    buffer_chunk_limit = config_param('size', 128*1024*1024)
    buffer_queue_limit = config_param('integer', 128)
    flush_interval = config_param('time', 1)

    _shutdown = False

    #Override this.
    chunk_class = None

    def start(self):
        self._queue = gqueue.Queue(self.buffer_queue_limit)
        self._map = defaultdict(self.chunk_class)
        gevent.spawn(self.run)

    def run(self):
        while not self._shutdown:
            # todo: flush にかかった時間に応じて次の sleep 時間を引く.
            gevent.sleep(self.flush_interval)
            self.flush()

    def emit(self, key, data, chain):
        top = self._map.get(key)
        if not top:
            top = self._map[key] = self.chunk_class(key)

        if len(top) + len(data) <= self.buffer_chunk_limit:
            chain.next()
            top += data
            return False

        if len(data) > self.buffer_chunk_limit:
            log.warn("Size of the emitted data exceeds buffer_chunk_limit.\n"
                     "This may occur problems in the output plugins ``at this server.``\n"
                     "To avoid problems, set a smaller number to the buffer_chunk_limit\n"
                     "in the forward output ``at the log forwarding server.``"
                     )

        nc = self.chunk_class(key)

        try:
            nc += data
            self._queue.put_nowait(top)
            self._map[key] = nc
            chain.next()  # What is chain?
            return len(self.queue) == 1
        except gqueue.Full:
            log.error("buffer_queue_limit is exceeded.")
            nc.purge()
            raise
        except:
            nc.purge()
            raise

    def keys(self):
        return self._map.keys()

    def flush(self):
        log.debug("flush: keys=%s", self._map.keys())
        map_ = self._map
        keys = list(map_.keys())
        for key in keys:
            chunk = map_.pop(key)
            self._queue.put(chunk) # Would block here.
        log.debug("flush: queue=%s", self._queue.qsize())

    def get(self, block=True, timeout=None):
        return self._queue.get(block, timeout)

    def get_nowait(self):
        return self._queue.get_nowait()

    def shutdown(self):
        self._shutdown = True
        self.flush()
