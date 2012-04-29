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

from collections import deque

class BufferChunk(object):
    pass

class Buffer(Configurable):
    def start(self):
        pass

    def shutdown(self):
        pass

    def before_shutdown(self, out):
        pass


class BasicBuffer(Buffer):

    buffer_chunk_limit = config_param('size', 128*1024*1024)
    buffer_queue_limit = config_param('integer', 128)

    def start(self):
        self._queue = deque()
        self._map = {}

