# coding: utf-8
"""
    fluenpy.command
    ~~~~~~~~~~~~~~~

    Entry point for fluenpy.

    :copyright: (c) 2012 by INADA Naoki
    :license: Apache v2
"""

from __future__ import print_function, division, absolute_import

import sys
from fluenpy.supervisor import Supervisor
from optparse import OptionParser

DEFAULT_CONFIG_PATH = '/etc/fluent/fluent.conf'

def make_parser():
    parser = OptionParser()
    option = parser.add_option
    option('-c', '--config', default=DEFAULT_CONFIG_PATH,
           help="config file path"
           )
    return parser

def main():
    parser = make_parser()
    opts, args = parser.parse_args()
    if args:
        parser.error("fluent.py doesn't accept commandline arguments.")
    Supervisor(opts).start()
