#!/usr/bin/python

import socket
import tornado.web

from handlers_base import *

class MirrorIndexHandler(BaseHandler):
	def get(self):
		ip_addr = self.get_argument("addr", self.request.remote_ip)

		# Get a list of all mirrors.
		all_mirrors = self.mirrors.get_all()

		# Choose the preferred ones by their location.
		preferred_mirrors = all_mirrors.get_for_location(ip_addr)

		# Remove the preferred ones from the list of the rest.
		other_mirrors = all_mirrors - preferred_mirrors

		self.render("mirrors.html",
			preferred_mirrors=preferred_mirrors, other_mirrors=other_mirrors)


class MirrorItemHandler(BaseHandler):
	def get(self, id):
		_ = self.locale.translate

		mirror = self.mirrors.get(id)
		if not mirror:
			raise tornado.web.HTTPError(404)

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
