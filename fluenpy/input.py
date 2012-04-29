# coding: utf-8
"""
    fluenpy.input
    ~~~~~~~~~~~~~

    Base class for input plugins.

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""

from __future__ import print_function, division, absolute_import, with_statement
import logging
import os

from fluenpy.config import Configurable

log = logging.getLogger(__name__)

class Input(Configurable):
    def start(self):
        pass

    def shutdown(self):
        pass
