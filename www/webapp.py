#!/usr/bin/python2.6

import tornado.httpserver
import tornado.ioloop

from webapp import Application
application = Application()

if __name__ == "__main__":
	http_server = tornado.httpserver.HTTPServer(application)
	http_server.listen(8080)

	try:
		tornado.ioloop.IOLoop.instance().start()
	except KeyboardInterrupt:
		# Shutdown mirror monitoring
		from webapp.mirrors import mirrors
		mirrors.shutdown()

		raise
