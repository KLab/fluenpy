# coding: utf-8
"""
    fluenpy.plugins.buf_memory
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""
from __future__ import print_function, division, absolute_import, with_statement
import logging
Log = logging.getLogger(__name__)

from fluenpy.plugin import Plugin
from fluenpy.buffer import BaseBufferChunk, BaseBuffer
from fluenpy.config import config_param

try:
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO


class MemoryBufferChunk(BaseBufferChunk):
    def __init__(self, key, expire):
        super(MemoryBufferChunk, self).__init__(key, expire)
        self._buf = BytesIO()

    def __iadd__(self, data):
        self._buf.write(data)
        return self

    def __len__(self):
        return self._buf.tell()

    def read(self):
        return self._buf.getvalue()

    def purge(self):
        self._buf = BytesIO()


class MemoryBuffer(BaseBuffer):

    buffer_chunk_limit = config_param("size", 32 * 1024**2)
    buffer_queue_limit = config_param("integer", 32)
    flush_interval = config_param('time', 5)

    def new_chunk(self, key, expire):
        return MemoryBufferChunk(key, expire)


Plugin.register_buffer('memory', MemoryBuffer)
