# coding: utf-8
"""
    fluenpy.plugins.out_stdout
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""
from __future__ import print_function, division, absolute_import, with_statement
import logging
log = logging.getLogger(__name__)

from fluenpy.plugin import Plugin
from fluenpy.output import Output
from fluenpy.config import config_param

from datetime import datetime
import json
import sys


class StdoutOutput(Output):

    autoflush = config_param('bool', False)

    def emit(self, tag, es, chain):
        for t, record in es:
            dt = datetime.fromtimestamp(t)
            print("%s %s: %s" % (dt, tag, json.dumps(record)))

        if self.autoflush:
            sys.stdout.flush()

        chain.next()

Plugin.register_output('stdout', StdoutOutput)
