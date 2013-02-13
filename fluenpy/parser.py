# coding: utf-8
"""
    fluenpy.parser
    ~~~~~~~~~~~~~~

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""

from __future__ import print_function, division, absolute_import, with_statement
import logging
log = logging.getLogger(__name__)

import re
import time
from fluenpy.error import ConfigError
from fluenpy.config import Configurable, config_param

try:
    from simplejson import loads
except ImportError:
    from json import loads


class RegexpParser(Configurable):
    time_format = config_param('string', None)

    def __init__(self, regexp, conf=None):
        self.regexp = regexp
        if conf is not None:
            self.configure(conf)

    def __call__(self, text):
        m = self.regexp.match(text)
        if not m:
            log.warn("pattern not match: pattern=%s, text=%r",
                     self.regexp.pattern, text)
            return None, None

        t = None
        record = {}

        for name, value in m.groupdict().iteritems():
            if value is None:
                continue
            if name == 'time':
                if self.time_format is not None:
                    t = time.mktime(time.strptime(value, self.time_format))
                else:
                    #TODO: Ruby だと Time.parse を使ってる.
                    #何か標準的なフォーマットでのパースを試行するべき.
                    t = float(value)
            else:
                record[name] = value

        if t is None:
            t = time.time()
        return t, record


class JSONParser(Configurable):
    time_key = config_param('string', 'time')
    time_format = config_param('string', None)

    def __call__(self, text):
        record = loads(text)

        t = None
        try:
            value = record.pop(self.time_key)
            if value:
                if self.time_format is not None:
                    t = time.mktime(time.strptime(value, self.time_format))
                else:
                    t = int(value)
        except KeyError:
            pass
        if t is None:
            t = time.time()

        return t, record

class ValuesParser(Configurable):
    time_key = config_param('string', None)
    time_format = config_param('string', None)

    def configure(self, conf):
        super(ValuesParser, self).configure(conf)

        self.keys = self.keys.split(',')

        if self.time_key and self.time_key not in self.keys:
            raise ConfigError("time_key %r is not included in keys %r" %
                              (self.time_key, self.keys))
        if self.time_format and not self.time_key:
            log.warn("time_format parameter is ignored because time_key parameter is not set")

    def record_map(self, record):
        t = None
        if self.time_key:
            value = record.pop(self.time_key)
            if self.time_format:
                t = time.mktime(time.strptime(value, self.time_format))
            else:
                #TODO: 一般的なフォーマットでのparseを試みる
                t = float(value)

        if t is None:
            t = time.time()
        return t, record

class TSVParser(ValuesParser):
    keys = config_param('string')
    delimiter = config_param('string', '\t')

    def __call__(self, text):
        record = dict(zip(self.keys, text.split(self.delimiter)))
        return self.record_map(record)

class LabeledTSVParser(ValuesParser):
    delimiter = config_param('string', '\t')
    label_delimiter = config_param('string', ':')

    def __call__(self, text):
        record = dict([c.split(self.label_delimiter, 1)
                       for c in text.split(self.delimiter)])
        return self.record_map(record)

#TODO: CSVParser
#TODO: ApacheParser

class ApacheParser(Configurable):

    REGEXP = re.compile(r"""^(?P<host>[^ ]*) [^ ]* (?P<user>[^ ]*) \[(?P<time>[^\]]*)\] "(?P<method>\S+)(?: +(?P<path>[^ ]*) +\S*)?" (?P<code>[^ ]*) (?P<size>[^ ]*)(?: "(?P<referer>[^\"]*)" "(?P<agent>[^\"]*)")?$""")

    def __call__(self, text):
        m = self.REGEXP.match(text)
        if not m:
            log.warn("pattern not match: %r", text)
            return None, None
        record = m.groupdict()

        for k in ('host', 'user', 'referer', 'agent'):
            if record[k] == '-':
                record[k] = None

        t = time.mktime(time.strptime(record['time'], "%d/%b/%Y:%H:%M:%S %z"))
        del record['time']

        try:
            record['code'] = int(record['code']) or None
        except ValueError:
            record['code'] = None
        try:
            record['size'] = int(record['size'])
        except ValueError:
            record['size'] = None

        return t, record


class TextParser(object):
    TEMPLATE_FACTORIES = {
        'apache': lambda: RegexpParser(r"""^(?P<host>[^ ]*) [^ ]* (?P<user>[^ ]*) \[(?P<time>[^\]]*)\] "(?P<method>\S+)(?: +(?P<path>[^ ]*) +\S*)?" (?P<code>[^ ]*) (?P<size>[^ ]*)(?: "(?P<referer>[^\"]*)" "(?P<agent>[^\"]*)")?$""", {'time_format': "%d/%b/%Y:%H:%M:%S %z"}),
        'apache2': lambda: ApacheParser(),
        'syslog': lambda: RegexpParser(r"""^(?P<time>[^ ]*\s*[^ ]* [^ ]*) (?P<host>[^ ]*) (?P<ident>[a-zA-Z0-9_\/\.\-]*)(?:\[(?P<pid>[0-9]+)\])?[^\:]*\: *(?P<message>.*)$""", {'time_format': "%b %d %H:%M:%S"}),
        'json': lambda: JSONParser(),
        'tsv': lambda: TSVParser(),
        'ltsv': lambda: LabeledTSVParser(),
        'nginx': lambda: RegexpParser(r"""^(?P<remote>[^ ]*) (?P<host>[^ ]*) (?P<user>[^ ]*) \[(?P<time>[^\]]*)\] "(?P<method>\S+)(?: +(?P<path>[^ ]*) +\S*)?" (?P<code>[^ ]*) (?P<size>[^ ]*)(?: "(?P<referer>[^\"]*)" "(?P<agent>[^\"]*)")?$""", {'time_format': "%d/%b/%Y:%H:%M:%S %z"}),
        #TODO: nginx
    }

    parser = None

    @classmethod
    def register_template(cls, name, regexp_or_proc, time_format=None):
        if callable(regexp_or_proc):
            factory = regexp_or_proc
        else:
            factory = lambda: RegexpParser(regexp_or_proc, {'time_format': time_format})
        cls.TEMPLATES[name] = factory

    def configure(self, conf, required=True):
        format = conf.get('format')
        if format is None:
            if required:
                raise ConfigError("'format' parameter is required")
            else:
                return None

        if format[0] == format[-1] == '/':  # regexp
            try:
                regexp = re.compile(format[1:-1])
                if not regexp.groupindex:
                    raise ConfigError("No named captures")
            except re.error as e:
                raise ConfigError("Invalid regexp %r: %s" % (format[1:-1], e))
            parser = RegexpParser(regexp)
        else:  # built-in template
            factory = self.TEMPLATE_FACTORIES.get(format)
            if factory is None:
                raise ConfigError("Unknown format template: %s" % (format,))
            parser = factory()

        if hasattr(parser, 'configure'):
            parser.configure(conf)
        self.parser = parser
        return True

    def parse(self, text):
        return self.parser(text)
