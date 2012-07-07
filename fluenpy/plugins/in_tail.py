# coding: utf-8
"""
    fluenpy.plugins.in_tail
    ~~~~~~~~~~~~~~~~~~~~~~~~

    tail from rotated log.

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""

from __future__ import print_function, division, absolute_import, with_statement
import logging
import os
import errno
import time

import gevent
from fluenpy.plugin import Plugin
from fluenpy.input import Input
from fluenpy.engine import Engine
from fluenpy.config import config_param

log = logging.getLogger(__name__)


class TailInput(Input):

    path = tag = key = config_param('string')
    rotate_wait = config_param('time', default=5)

    def start(self):
        self._shutdown = False
        self._proc = gevent.spawn(self.run)

    @property
    def paths(self):
        return self._paths

    def configure(self, conf):
        super(TailInput, self).configure(conf)
        self._path = self.path.strip()

    def emit(self, line):
        Engine.emit(self.tag, int(time.time()), {self.key: line})

    def run(self):
        path = self._path
        fd = None
        before = b''
        try:
            while not self._shutdown:
                if fd is None:
                    try:
                        fd = os.open(path, os.O_NONBLOCK)
                        log.debug("Opened log file.")
                    except OSError:
                        log.debug("Couldn't open log file.")
                        gevent.sleep(self.rotate_wait)
                        continue

                buf = self.readsome(fd)

                if not buf:
                    if self.is_current(fd):
                        gevent.sleep(0.3)
                        continue
                    else:
                        gevent.sleep(self.rotate_wait)
                        buf = self.readsome(fd)
                        if not buf:
                            os.close(fd)
                            fd = None
                            log.debug("Closed log file.")
                            continue

                if b'\n' not in buf:
                    before += buf
                    continue

                buf = before + buf
                before = b''
                lines = buf.splitlines(True)

                if not lines[-1].endswith(b'\n'):
                    before = lines.pop()

                for line in lines:
                    self.emit(line.rstrip())
        finally:
            if fd is not None:
                os.close(fd)

    def is_current(self, fd):
        try:
            ino = os.stat(self._path).st_ino
        except OSError:
            return False
        else:
            return ino == os.fstat(fd).st_ino

    def readsome(self, fd):
        while 1:
            try:
                return os.read(fd, 1024**2)
            except OSError as e:
                if e.errno == errno.EAGAIN:
                    gevent.sleep(0.2)
                    continue
                raise


Plugin.register_input('tail', TailInput)
