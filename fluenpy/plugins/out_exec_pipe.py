# coding: utf-8
"""
    fluenpy.plugins.out_exec_pipe
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""
from __future__ import print_function, division, absolute_import, with_statement
import logging
log = logging.getLogger(__name__)

import os
from fluenpy.config import config_param
from fluenpy.output import BufferedOutput
from fluenpy.plugin import Plugin

try:
    import gevent.subprocess as subprocess
except ImportError:
    # may block. don't use this when gevent 1.0b3 is released.
    import subprocess


class ExecPipeOutput(BufferedOutput):

    command = config_param('string')

    def start(self):
        preexec = getattr(os, 'setsid', None)
        self._proc = subprocess.Popen(self.command, shell=True,
                                      stdin=subprocess.PIPE,
                                      preexec_fn=preexec)
        super(ExecPipeOutput, self).start()

    def shutdown(self):
        super(ExecPipeOutput, self).shutdown()
        self._proc.stdin.close()
        self._proc.wait()
        self._proc = None

    def write(self, chunk):
        self._proc.stdin.write(chunk.read())


Plugin.register_output('exec_pipe', ExecPipeOutput)

