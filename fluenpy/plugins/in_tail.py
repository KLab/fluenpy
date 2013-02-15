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
import re

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

class PositionFile(object):
    def __init__(self, file, map, last_pos):
        self.file = file
        self.map = map
        self.last_pos = last_pos

    def __getitem__(self, path):
        m = self.map.get(path)
        if m is not None:
            return m

        f = self.file
        f.seek(self.last_pos)
        f.write(path + b"\t")
        offset = f.tell()
        f.write("0000000000000000\t00000000\n")
        self.last_pos = f.tell()
        self.map[path] = FilePositionEntry(f, offset)

    @classmethod
    def parse(cls, file):
        map = {}
        file.seek(0)
        r = re.compile("^([^\t]+)\t([0-9a-fA-F]+)\t([0-9a-fA-F]+)")
        for line in file:
            m = r.match(line)
            if not m:
                continue
            path = m.group(1)
            #pos = int(m.group(2), 16)
            #inode = int(m.group(3), 16)
            offset = file.tell() - len(line) + len(path) + 1
            map[path] = FilePositionEntry(file, offset)
        return cls(file, map, file.tell())

class MemoryPositionEntry(object):
    def __init__(self):
        self.pos = self.inode = 0

    def update(self, inode, pos):
        self.inode = inode
        self.pos = pos

    def update_pos(self, pos):
        self.pos = pos

    def read_pos(self):
        return self.pos

    def read_inode(self):
        return self.inode

class FilePositionEntry(object):
    POS_SIZE = 16
    INO_OFFSET = 17
    INO_SIZE = 8
    LN_OFFSET = 25
    SIZE = 26

    def __init__(self, file, offset):
        self.file = file
        self.offset = offset

    def update(self, inode, pos):
        self.file.seek(self.offset)
        self.file.write(b"%016x\t%08x" % (pos, inode))
        self.inode = inode

    def update_pos(self, pos):
        self.file.seek(self.offset)
        self.file.write("b%016x" % (pos,))

    def read_inode(self):
        self.file.seek(self.offset + self.INO_OFFSET)
        return int(self.file.read(8), 16)

    def read_pos(self):
        self.file.seek(self.offset)
        return int(self.file.read(16), 16)


Plugin.register_input('tail', TailInput)
