# coding: utf-8
"""
    fluenpy.engine
    ~~~~~~~~~~~~~~~

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""

from __future__ import print_function, division, absolute_import, with_statement
import logging
import os

from fluenpy.match import Match, NoMatch
from fluenpy.plugin import Plugin
from fluenpy import config
from fluenpy.error import ConfigError
import gevent

log = logging.getLogger(__name__)


class EngineClass(object):
    def __init__(self):
        self._matches = []
        self._sources = []
        self._match_cache = {}
        self._started = []

    def read_config(self, path):
        with open(path) as f:
            self.parse_config(f, os.path.basename(path), os.path.dirname(path))

    def parse_config(self, file, fname, basepath):
        conf = config.parse(file, fname, basepath)
        self.configure(conf)
        for elem, key in conf.not_fetched():
            log.warn("parameter %r in %s is not used.", key, elem)

    def _config_source(self, elem):
        type = elem['type']
        if not type:
            raise ConfigError("Missing 'type' parameter on <source> directive")
        log.info("adding source type=%r", type)
        in_ = Plugin.new_input(type)
        in_.configure(elem)
        self._sources.append(in_)

    def _config_match(self, elem):
        type = elem['type']
        pattern = elem.arg
        if not type:
            raise ConfigError(
                    "Missing 'type' parameter on <match %s> directive",
                    pattern)
        log.info("adding match %r => %r", pattern, type)

        out = Plugin.new_output(type)
        out.configure(elem)
        match = Match(pattern, out)
        self._matches.append(match)

    def configure(self, conf):
        Plugin.load_plugins()
        for elem in conf.elements:
            if elem.name == 'source':
                self._config_source(elem)
            elif elem.name == 'match':
                self._config_match(elem)

    def emit(self, tag, time, record):
        self.emit_stream(tag, [(time, record)])

    def emit_stream(self, tag, array):
        try:
            target = self._match_cache.get(tag, None)
            if target is None:
                target = self.match(tag) or NoMatch.instance
                if len(self._match_cache) < 1024:
                    self._match_cache[tag] = target
            target.emit(tag, array)
        except Exception as e:
            log.warn("emit transaction failed. error=%s", e)
            raise

    def match(self, tag):
        for m in self._matches:
            if m.match(tag):
                return m
        return None

    def run(self):
        for m in self._matches:
            m.start()
        for s in self._sources:
            s.start()
        while 1:
            gevent.sleep(1)

Engine = EngineClass()
