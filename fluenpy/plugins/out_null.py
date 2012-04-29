# coding: utf-8
"""
    fluenpy.plugins.out_null
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""
from __future__ import print_function, division, absolute_import, with_statement
import logging
log = logging.getLogger(__name__)

from fluenpy import error
from fluenpy.output import Output
from fluenpy.plugin import Plugin


class NullOutput(Output):
    def emit(self, tag, es, chain):
        chain.next()
