#!/usr/bin/python2.6

import tornado.httpserver
import tornado.ioloop

from webapp import Application
application = Application()

if __name__ == "__main__":
	http_server = tornado.httpserver.HTTPServer(application, xheaders=True)
	http_server.listen(8001)

	try:
		tornado.ioloop.IOLoop.instance().start()
	except KeyboardInterrupt:
		# Shutdown mirror monitoring
		from webapp.mirrors import mirrors
		mirrors.shutdown()

		raise
