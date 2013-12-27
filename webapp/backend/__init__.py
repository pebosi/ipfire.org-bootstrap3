#!/usr/bin/python

from tornado.options import define, options, parse_command_line

# Command line options
define("debug", default=False, help="Run in debug mode", type=bool)
parse_command_line()

from base import Backend
