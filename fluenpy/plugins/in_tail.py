# coding: utf-8
"""
    fluenpy.plugins.in_tail
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Base class for input plugins.

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""

from __future__ import print_function, division, absolute_import, with_statement
import logging
import os

from fluenpy.plugin import Plugin
from fluenpy.input import Input
from fluenpy.config import config_param
from gevent import sleep

log = logging.getLogger(__name__)


class TailInput(Input):

    path = tag = config_param('string')
    rotate_wait = config_param('time', default=5)
    pos_file = config_param('string', default=None)

    @property
    def paths(self):
        return self._paths

    def configure(self, conf):
        super(TailInput, self).configure(conf)

        self._paths = [p.strip() for p in self.path.split(',')]
        if not self._paths:
            raise ConfigError("tail: 'path' parameter is required on tail input")

        if self.pos_file:
            raise ConfigError("tail: pos_file is not supported yet.")
            #self._pf_file = open(self.pos_file, 'a+', 0)
            #self._pf_file.seek(0)


Plugin.register_input('tail', TailInput)
