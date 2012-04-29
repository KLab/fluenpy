# coding: utf-8
"""
    fluenpy.plugins.in_http
    ~~~~~~~~~~~~~~~~~~~~~~~

    Input from http.

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""
from __future__ import print_function, division, absolute_import, with_statement
import logging
log = logging.getLogger(__name__)
import os
import cgi
import time

from fluenpy.engine import Engine
from fluenpy.plugin import Plugin
from fluenpy.input import Input
from fluenpy.config import config_param
from gevent.pywsgi import WSGIServer


class Httpinput(Input):

    port = config_param('integer', 9880)
    bind = config_param('string', '0.0.0.0')
    # TODO: body_size_limit, keepalive_timeout

    def wsgi_app(self, env, start):
        path = env['PATH_INFO'].strip('/')
        tag = path.replace('/', '.')
        content_type = env.get('CONTENT_TYPE', '')
        params = dict(cgi.parse_qsl(env['QUERY_STRING']))
        input = env['wsgi.input']

        if content_type.startswith('application/x-www-form-urlencoded'):
            params.update(cgi.parse_qs(input.read()))
        elif content_type.startswith('multipart/form-data'):
            fs = cgi.FieldStorage(input, environ=env)
            for k in fs.keys():
                params[k] = fs.getfirst(k)
        elif content_type.startswith('application/json'):
            params['json'] = input.read()

        if 'msgpack' in params:
            record = msgpack.unpackb(params['msgpack'])
        elif 'json' in params:
            record = json.loads(params['json'])
        else:
            record = params

        if 'time' in params:
            time_ = int(params['time'])
        else:
            time_ = int(time.time())

        log.debug("Recieve message: tag=%r, record=%r", tag, record)
        Engine.emit(tag, time_, record)

        start("200 OK", [('Content-Type', 'text/plain')])
        return [""]

    def start(self):
        log.info("start http server on %s:%s", self.bind, self.port)
        self._server = server = WSGIServer((self.bind, self.port), self.wsgi_app, log=None)
        server.start()

    def shutdown(self):
        self._server.stop()

Plugin.register_input('http', Httpinput)
