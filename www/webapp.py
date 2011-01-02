#!/usr/bin/python2.6

import daemon
import logging
import logging.handlers
import os
import signal
import sys

#import tornado.httpserver
#import tornado.ioloop
import tornado.options

from webapp import Application

if __name__ == "__main__":
	app = Application()

	context = daemon.DaemonContext(
		working_directory=os.getcwd(),
#		stdout=sys.stdout, stderr=sys.stderr, # XXX causes errors...
	)

	context.signal_map = {
		signal.SIGHUP  : app.reload,
		signal.SIGTERM : app.shutdown,
	}

#	with context:
#		app.run()

	app.run()
