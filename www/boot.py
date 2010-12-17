#!/usr/bin/python

import logging
import os
import tornado.httpserver
import tornado.ioloop
import tornado.locale
import tornado.options
import tornado.web

from webapp import backend

BASEDIR = os.path.dirname(__file__)

# Enable logging
tornado.options.enable_pretty_logging()
tornado.options.parse_command_line()

def word_wrap(s, width=65):
	paragraphs = s.split('\n')
	lines = []
	for paragraph in paragraphs:
		while len(paragraph) > width:
			pos = paragraph.rfind(' ', 0, width)
			if not pos:
				pos = width
			lines.append(paragraph[:pos])
			paragraph = paragraph[pos:]
		lines.append(paragraph)
	return '\n'.join(lines)

class BaseHandler(tornado.web.RequestHandler):
	@property
	def netboot(self):
		return backend.NetBoot()


class MenuGPXEHandler(BaseHandler):
	"""
		menu.gpxe
	"""
	def get(self):
		# XXX Check if version of the bootloader is allright

		# Devliver content
		self.set_header("Content-Type", "text/plain")
		self.write("#!gpxe\n")
		self.write("chain menu.c32 premenu.cfg\n")


class MenuCfgHandler(BaseHandler):
	def _menu_string(self, menu, level=0):
		s = ""

		for entry in menu:
			s += self._menu_entry(entry, level=level)

		return s

	def _menu_entry(self, entry, level=0):
		lines = []

		ident = "\t" * level

		if entry.type == "seperator":
			lines.append(ident + "menu separator")

		elif entry.type == "header":
			lines.append(ident + "menu begin %d" % entry.id)
			lines.append(ident + "\tmenu title %s" % entry.title)

			# Add "Back..." entry
			lines.append(ident + "\tlabel %d.back" % entry.id)
			lines.append(ident + "\t\tmenu label Back...")
			lines.append(ident + "\t\tmenu exit")
			lines.append(ident + "\tmenu separator")

			lines.append("%s" % self._menu_string(entry.submenu, level=level+1))
			lines.append(ident + "menu end")

		elif entry.type == "config":
			lines.append(ident + "label %d" % entry.id)
			lines.append(ident + "\tmenu label %s" % entry.title)
			if entry.description:
				lines.append(ident + "\ttext help")
				lines.append(word_wrap(entry.description))
				lines.append(ident + "\tendtext")
			lines.append(ident + "\tkernel /config/%s/boot.gpxe" % entry.item)

		return "\n".join(lines + [""])

	def get(self):
		self.set_header("Content-Type", "text/plain")

		menu = self._menu_string(self.netboot.get_menu(1))

		self.render("menu.cfg", menu=menu)


class BootGPXEHandler(BaseHandler):
	def get(self, id):
		config = self.netboot.get_config(id)
		if not config:
			raise tornado.web.HTTPError(404, "Configuration with ID '%s' was not found" % id)

		lines = ["#!gpxe", "imgfree",]

		line = "kernel -n img %s" % config.image1
		if line.endswith(".iso"):
			line += " iso"
		lines.append(line)

		if config.image2:
			lines.append("initrd -n img %s" % config.image2)

		lines.append("boot img")

		for line in lines:
			self.write("%s\n" % line)


class Application(tornado.web.Application):
	def __init__(self):
		settings = dict(
			debug = True,
			gzip = True,
			static_path = os.path.join(BASEDIR, "static/netboot"),
			template_path = os.path.join(BASEDIR, "templates/netboot"),
		)

		tornado.web.Application.__init__(self, **settings)

		self.add_handlers(r"boot.ipfire.org", [
			# Configurations
			(r"/files/menu.gpxe", MenuGPXEHandler),
			(r"/files/menu.cfg", MenuCfgHandler),
			(r"/config/([0-9]+)/boot.gpxe", BootGPXEHandler),

			# Static files
			(r"/files/(boot.png|premenu.cfg|vesamenu.c32|menu.c32)",
				tornado.web.StaticFileHandler, { "path" : self.settings["static_path"] }),
		])

	@property
	def ioloop(self):
		return tornado.ioloop.IOLoop.instance()

	def shutdown(self, *args):
		logging.debug("Caught shutdown signal")
		self.ioloop.stop()

	def run(self, port=8002):
		logging.debug("Going to background")

		# All requests should be done after 30 seconds or they will be killed.
		self.ioloop.set_blocking_log_threshold(30)

		http_server = tornado.httpserver.HTTPServer(self, xheaders=True)

		# If we are not running in debug mode, we can actually run multiple
		# frontends to get best performance out of our service.
		if not self.settings["debug"]:
			http_server.bind(port)
			http_server.start(num_processes=4)
		else:
			http_server.listen(port)

		self.ioloop.start()

if __name__ == "__main__":
	a = Application()

	a.run()

