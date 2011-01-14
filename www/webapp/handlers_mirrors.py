#!/usr/bin/python

import socket
import tornado.web

from handlers_base import *

class MirrorIndexHandler(BaseHandler):
	def get(self):
		mirrors = self.mirrors.list()

		self.render("mirrors.html", mirrors=mirrors)


class MirrorItemHandler(BaseHandler):
	def get(self, id):
		mirror = self.mirrors.get(id)
		if not mirror:
			raise tornado.web.HTTPError(404)

		ip = socket.gethostbyname(mirror.hostname)
		mirror.location = self.geoip.get_all(ip)

		# Shortcut for coordiantes
		mirror.coordiantes = "%s,%s" % \
			(mirror.location.latitude, mirror.location.longitude)

		# Nice string for the user
		mirror.location_str = mirror.location.country_code
		if mirror.location.city:
			mirror.location_str = "%s, %s" % \
				(mirror.location.city, mirror.location_str)

		self.render("mirrors-item.html", item=mirror)


class MirrorHandler(BaseHandler):
	def get(self):
		self.redirect("mirrors/all")


class MirrorAllHandler(BaseHandler):
	def get(self):
		self.render("downloads-mirrors.html", mirrors=self.mirrors.list())


class MirrorDetailHandler(BaseHandler):
	def get(self, id):
		self.render("download-mirror-detail.html", mirror=self.mirrors.get(id))
