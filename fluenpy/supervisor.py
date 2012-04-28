# coding: utf-8
"""
    fluenpy.supervisor
    ~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""

from __future__ import print_function, division, absolute_import

import fluenpy.engine import Engine

class Supervisor(object):
    def __init__(self, opts):
        self._opts = opts
        self._finished = False

    def start(self):
        #todo: supervise
        self._engine = engine = Engine()
        engine.read_config(opts.config)
        engine.run()
