# coding: utf-8
"""
    fluenpy.plugins.buf_memory
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""
from __future__ import print_function, division, absolute_import, with_statement
import logging
log = logging.getLogger(__name__)

from fluenpy import error
from fluenpy.plugin import Plugin
from fluenpy.buffer import BufferChunk, BasicBuffer
from fluenpy.config import config_param

try:
    # Python 2.6 では io.BytesIO は Python で実装されているので、
    # cStringIO の方を優先.
    from cStringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO


class MemoryBufferChunk(BufferChunk):
    def __init__(self, key, data=b''):
        super(MemoryBufferChunk, self).__init__(key)
        self._data = bytearray(data)

    def __lshift__(self, data):
        self._data += data
        return self

    def __len__(self):
        return len(self._data)

    def read(self):
        return self._data

    def open(self):
        return BytesIO(self._data)

class MemoryBuffer(BasicBuffer):

    buffer_chunk_limit = config_param("size", 32 * 1024**2)
    buffer_queue_limit = config_param("integer", 32)

    def new_chunk(self, key):
        return MemoryBufferChunk(key)

Plugin.register_buffer('memory', MemoryBuffer)
