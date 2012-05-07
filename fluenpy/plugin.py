# coding: utf-8
"""
    fluenpy.plugin
    ~~~~~~~~~~~~~~~

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""

from __future__ import print_function, division, absolute_import, with_statement
import logging
import os
import imp
import glob

import fluenpy.plugins
from fluenpy.config import Configurable

log = logging.getLogger(__name__)

class PluginClass(object):
    def __init__(self):
        self._input = {}
        self._output = {}
        self._buffer = {}

    def register_input(self, type, klass):
        self._input[type] = klass
        log.debug("registered input plugin %r", type)

    def register_output(self, type, klass):
        self._output[type] = klass
        log.debug("registered output plugin %r", type)

    def register_buffer(self, type, klass):
        self._buffer[type] = klass
        log.debug("registered buffer plugin %r", type)

    def new_input(self, type):
        return self._input[type]()

    def new_output(self, type):
        return self._output[type]()

    def new_buffer(self, type):
        return self._buffer[type]()

    def load_plugins(self):
        loaded = set()
        for path in fluenpy.plugins.__path__:
            for suff, _, _ in imp.get_suffixes():
                for modpath in glob.glob(path + "/*" + suff):
                    modname = os.path.basename(modpath)
                    modname = modname[:-len(suff)]
                    if modname in loaded or modname.startswith('_'):
                        continue
                    log.debug("loading %r", modname)
                    try:
                        __import__('fluenpy.plugins.' + modname)
                        loaded.add(modname)
                    except Exception as e:
                        log.error("failed to import %s: %s", modname, e)

    def add_plugin_dir(self, path):
        path = os.path.expanduser(path)
        path = os.path.expandvars(path)
        path = path.rstrip('/')
        if path not in fluenpy.plugins.__path__:
            fluenpy.plugins.__path__.append(path)


Plugin = PluginClass()
