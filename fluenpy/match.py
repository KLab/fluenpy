# coding: utf-8
"""
    fluenpy.match
    ~~~~~~~~~~~~~~

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""
from __future__ import print_function, division, absolute_import, with_statement
import logging
log = logging.getLogger(__name__)

import re
import fnmatch


class Match(object):
    def __init__(self, pattern, output):
        self.output = output

        patterns = pattern.split()
        rex = map(fnmatch.translate, pattern.split())
        rex = ')|('.join(rex)
        rex = '\\A((' + rex + '))\\Z'
        self._rex = re.compile(rex)

    def match(self, tag):
        return self._rex.match(tag) is not None

    def emit(self, tag, es):
        self.output.emit(tag, es)

    def start(self):
        self.output.start()

    def shutdown(self):
        self.output.shutdown()


class NoMatch(object):
    def match(self, s):
        return True

    def emit(self, tag, es):
        pass

    def start(self):
        pass

    def shutdown(self):
        pass

NoMatch.instance = NoMatch()
