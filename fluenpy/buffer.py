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

from fluenpy.config import Configurable, config_param

import gevent.queue
from time import time as now

try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO


class BaseBufferChunk(object):
    def __init__(self, key, expire):
        self.key = key
        self.expire = expire

    def __iadd__(self, data):
        """Append *data* to this chunk."""
        raise NotImplemented

    def __len__(self):
        """Return bytesize of this chunk."""
        raise NotImplemented

    def read(self):
        """Return data written to this chunk."""
        raise NotImplemented

    def open(self):
        """Return file-like readable object for this chunk."""
        return BytesIO(self.read())

    def purge(self):
        """Called when throw away this chunk."""
        pass


class BaseBuffer(Configurable):

    buffer_chunk_limit = config_param('size', 128*1024*1024)
    buffer_queue_limit = config_param('integer', 128)
    flush_interval = config_param('time', 60)

    _shutdown = False

    def new_chunk(self, key, expire):
        raise NotImplemented

    def start(self):
        self._queue = gevent.queue.Queue(self.buffer_queue_limit)
        self._map = {}
        gevent.spawn(self.run)

    def run(self):
        # flush を実行する間隔
        check_interval = min(self.flush_interval/2, 2)
        while not self._shutdown:
            gevent.sleep(check_interval)
            self.flush(force=False)

    def emit(self, key, data, chain):
        top = self._map.get(key)
        if not top:
            top = self._map[key] = self.new_chunk(key, now()+self.flush_interval)

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

        nc = self.new_chunk(key, now()+self.flush_interval)

        try:
            nc += data
            self._map[key] = nc
            self._queue.put_nowait(top)
            chain.next()  # What is chain?
        except gqueue.Full:
            log.error("buffer_queue_limit is exceeded.")
        except:
            nc.purge()
            raise

    def keys(self):
        return self._map.keys()

    def flush(self, force=True):
        u"""バッファリング中のチャンクを書きこみ待ちキューへ移動する.
        *force* が true のときはすべてのチャンクを移動し、 false の時は
        chunk.expire が古いものだけをフラッシュする.
        """
        map_ = self._map
        keys = list(map_.keys())
        t = now()
        for key in keys:
            chunk = map_[key]
            if not force and chunk.expire > t:
                continue
            del map_[key]
            self._queue.put(chunk) # Would block here.
            gevent.sleep(0) # give a chance to write.
        if keys:
            log.debug("flush: queue size=%s", self._queue.qsize())

    def get(self, block=True, timeout=None):
        return self._queue.get(block, timeout)

    def get_nowait(self):
        return self._queue.get_nowait()

    def shutdown(self):
        self._shutdown = True
        self.flush()
