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
from fluenpy.output import NullOutputChain


class Match(object):
    def __init__(self, pattern, output):
        patterns = map(MatchPattern, pattern)
        if len(patterns) == 1:
            self._pattern = patterns[0]
        else:
            self._pattern = OrMatchPattern(patterns)

        self.output = output

    def match(self, tag):
        return self._pattern.match(tag)

    def emit(self, tag, es):
        chain = NullOutputChain
        self.output.emit(tag, es, chain)

    def start(self):
        self.output.start()

    def shutdown(self):
        self.output.shutdown()


class MatchPattern(object):
    def __init__(self, pattern):
        self._r = re.compile(fnmatch.translate(pattern))

    def match(self, s):
        return self._r.match(s) is not None

class OrMatchPattern(object):
    def __init__(self, patterns):
        self._patterns = patterns

    def match(self, s):
        return any(p.match(s) for p in self._patterns)


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
