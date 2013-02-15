# coding: utf-8
"""
    fluenpy.plugins.in_multilog
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    tail from multilog.

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""

from __future__ import print_function, division, absolute_import, with_statement
import logging
import os
import errno
import glob

from fluenpy.plugin import Plugin
from fluenpy.input import Input
from fluenpy.engine import Engine
from fluenpy.config import config_param
import gevent
import gdbm

log = logging.getLogger(__name__)

def _open_nonblock(path):
    return os.open(path, os.O_NONBLOCK)


class MultilogInput(Input):

    dir = tag = key = config_param('string')
    pos_file = config_param('string')

    def start(self):
        self._shutdown = False
        self._proc = gevent.spawn(self.run)

    def _open_log(self, inode=None, offset=None):
        pat = os.path.join(self.dir, '@*.s')
        current = os.path.join(self.dir, 'current')
        files = glob.glob(pat) + [current]
        files.sort()
        target = None
        if inode:
            for f in files:
                st = os.stat(f)
                if st.st_ino == inode:
                    target = f
                    break
        if not target:
            target = files[0]
            offset = 0

        fd = _open_nonblock(target)
        if offset:
            os.lseek(fd, offset, 0)
        return os.fstat(fd).st_ino, fd, offset

    def _open_next(self, fd):
        current = os.path.join(self.dir, 'current')
        current_fd = _open_nonblock(current)

        pat = os.path.join(self.dir, '@*.[su]')
        files = glob.glob(pat)
        files.sort()
        files.append(current)

        inode = os.fstat(fd).st_ino
        os.close(fd)

        for idx, f in enumerate(files):
            if os.stat(f).st_ino == inode:
                break
        else:
            log.warn("multilog: can't find before file. (inode=%d)", inode)
            return os.fstat(current_fd).st_ino, current_fd

        idx += 1
        if len(files) == idx:
            log.warn("multilog: rotate current => current?")
            return os.fstat(current_fd).st_ino, current_fd

        next_file = files[idx]
        if next_file == current:
            return os.fstat(current_fd).st_ino, current_fd

        os.close(current_fd)
        return os.stat(next_file).st_ino, _open_nonblock(next_file)

    def is_current(self, fd):
        current = os.path.join(self.dir, 'current')
        current_ino = os.stat(current).st_ino
        ino = os.fstat(fd).st_ino
        log.debug("current inode=%d, fd inode=%d", current_ino, ino)
        return ino == current_ino

    def readsome(self, fd):
        while 1:
            try:
                return os.read(fd, 1024**2)
            except OSError as e:
                if e.errno == errno.EAGAIN:
                    gevent.sleep(0.2)
                    continue
                raise

    def emit(self, line):
        tai, line = line.split(' ', 1)
        tai = int(tai[1:17], 16)
        if tai >= 2**62:
            tai -= 2**62
        else:
            tai = 0
        Engine.emit(self.tag, tai, {self.key: line})

    def run(self):
        db = gdbm.open(self.pos_file, 'cs')
        fd = None
        before = b''

        if 'pos' in db:
            pos = db['pos']
            inode, offset = map(int, pos.split(' '))
        else:
            inode = None
            offset = 0

        inode, fd, offset = self._open_log(inode, offset)
        read_pos = offset
        try:
            while not self._shutdown:
                buf = self.readsome(fd)

                if not buf:
                    if self.is_current(fd):
                        log.debug("waiting current. offset=%d", offset)
                        gevent.sleep(0.3)
                    else:
                        inode, fd = self._open_next(fd)
                        offset = 0
                    continue

                offset += len(buf)
                if '\n' not in buf:
                    before += buf
                    continue

                read_pos = offset
                lines = buf.splitlines(True)
                del buf
                lines[0] = before + lines[0]
                before = b''

                last = lines[-1]
                if not last.endswith('\n'):
                    read_pos -= len(last)
                    before = last
                    del lines[-1]

                for line in lines:
                    self.emit(line.rstrip())
                db['pos'] = "%d %d" % (inode, read_pos)
        finally:
            db['pos'] = '%d %d' % (inode, read_pos)
            db.close()
            if fd is not None:
                os.close(fd)

    def shutdown(self):
        self._shutdown = True
        self._proc.join()


Plugin.register_input('multilog', MultilogInput)
