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
from fluenpy.parser import TextParser

log = logging.getLogger(__name__)


class TailInput(Input):

    path = tag = config_param('string')
    rotate_wait = config_param('time', default=5)
    pos_file = config_param('string', None)

    def __init__(self):
        self._paths = []
        self._pf_file = None
        self._pf = None

    def start(self):
        self._shutdown = False
        self._proc = gevent.spawn(self.run)

    @property
    def paths(self):
        return self._paths

    def configure(self, conf):
        super(TailInput, self).configure(conf)
        self._paths = [p.strip() for p in self.path.split(',')]

        if self.pos_file:
            self._pf_file = open(self.pos_file, 'r+b', 0)
            self._pf = PositionFile.parse(self.pf_file)
        else:
            log.warn("'pos_file PATH' parameter is not set to a 'tail' source.")
            log.warn("this parameter is highly recommended to save the position to resume tailing.")

        self.parser = TextParser()
        self.parser.configure(conf)

    def receive_lines(self, lines):
        lines = map(self.parser.parse, lines)
        Engine.emit_stream(self.tag, lines)

    def run(self):
        watchers = []
        threads = []
        for path in self._paths:
            pe = self._pf[path] if self._pf else None
            w = TailWatcher(path, self.rotate_wait, pe, self.receive_lines)
            watchers.append(w)
            threads.append(gevent.spawn(w.run))

        gevent.joinall(self.watchers)


class TailWatcher(object):
    def __init__(self, path, rotate_wait, position_entry, callback):
        self.path = path
        self.rotate_wait = rotate_wait
        self.position_entry = position_entry
        self.callback = callback
        self.stop = False
        self.buf = b''
        self.fd = None

    def run(self):
        first = True
        fd = None
        try:
            while not self.stop:
                self.ensure_open(first)
                first = False
                if not self.fd:
                    gevent.sleep(self.rotate_wait)
                    continue

                self.tail(fd)
                if self.is_current(fd):
                    gevent.sleep(0.2)
                    continue

                # rotate
                gevent.sleep(self.rotate_wait)
                self.tail(fd)
                os.close(fd)
                fd = None
                if self.buf:
                    self.receive_lines([self.buf])
                    self.buf = b''
        finally:
            if fd is not None:
                os.close(fd)

    def ensure_open(self, first):
        if self.fd:
            return self.fd
        try:
            self.fd = fd = os.open(self.path, os.O_NONBLOCK)
            log.debug("Opened log file: %s", self.path)
            st = os.fstat(fd)
            if first:
                if st.st_ino == self.position_entry.read_inode():
                    # seek to saved position
                    self.pos = self.position_entry.read_pos()
                else:
                    # begin tailing.
                    self.pos = st.st_size
                    self.position_entry.update(st.st_ino, self.pos)
                os.lseek(fd, self.pos, os.SEEK_SET)
            else:
                # rotate
                self.pos = 0
                self.position_entry(st.st_ino, 0)
        except OSError:
            log.debug("Couldn't open log file: %s", self.path)
            return None

    def tail(self, fd):
        buf = self.buf
        while True:
            read = self.readsome(fd)
            if not read:
                break
            self.pos += len(read)
            buf += read
            read = None
            lines = buf.splitlines(True)
            if not lines[-1].endswith(b'\n'):
                buf = lines.pop()
            else:
                buf = b''
            self.callback(lines)
            self.position_entry.update_pos(self.pos - len(buf))
        self.buf = buf

    def is_current(self, fd):
        try:
            ino = os.stat(self.path).st_ino
        except OSError:
            return False
        else:
            return ino == os.fstat(fd).st_ino

    def readsome(self, fd):
        while 1:
            try:
                return os.read(fd, 8000)
            except OSError as e:
                if e.errno == errno.EAGAIN:
                    gevent.sleep(0.1)
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
