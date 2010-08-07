#!/usr/bin/python2.6

import daemon
import logging
import logging.handlers
import os
import signal
import sys

import tornado.httpserver
import tornado.ioloop
import tornado.options

from webapp import Application

tornado.options.parse_command_line()

def setupLogging():
	formatter = logging.Formatter("%(asctime)s %(levelname)8s %(message)s")

	#handler = logging.handlers.RotatingFileHandler("webapp.log",
	#	maxBytes=10*1024**2, backupCount=5)
	handler = logging.FileHandler("webapp.log")

	handler.setFormatter(formatter)
	logging.getLogger().addHandler(handler)

if __name__ == "__main__":
	setupLogging()
	app = Application()

	context = daemon.DaemonContext(
		working_directory=os.getcwd(),
		stdout=sys.stdout, stderr=sys.stderr, # XXX causes errors...
	)

	context.signal_map = {
		signal.SIGHUP  : app.reload,
		signal.SIGTERM : app.stop,
	}

	with context:
		app.run()
