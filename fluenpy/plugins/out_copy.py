# coding: utf-8
"""
    fluenpy.plugins.out_copy
    ~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""

from __future__ import print_function, division, absolute_import, with_statement
import logging
log = logging.getLogger(__name__)

import traceback
from fluenpy import error
from fluenpy.output import Output
from fluenpy.plugin import Plugin


class CopyOutput(Output):

    def __init__(self):
        super(CopyOutput, self).__init__()
        self._outputs = []

    def configure(self, conf):
        for e in conf.elements:
            if e.name != "store":
                continue
            type_ = e.get('type')
            if type_ is None:
                raise error.ConfigError("Missing 'type' parameter on <store> directive")
            log.debug("adding store type=%r", type_)

            output = Plugin.new_output(type_)
            output.configure(e)
            self._outputs.append(output)
    
    def start(self):
        for o in self._outputs:
            o.start()

    def shutdown(self):
        for o in self._outputs:
            try:
                o.shutdown()
            except Exception:
                log.error("Error occured while shutdown:")
                log.error(traceback.format_exc())

    def emit(self, tag, es):
        for o in self._outputs:
            try:
                o.emit(tag, es)
            except Exception:
                log.error("Error occured while emit:")
                log.error(traceback.format_exc())


Plugin.register_output('copy', CopyOutput)
