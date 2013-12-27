#!/usr/bin/python

import socket
import tornado.web

from handlers_base import *

class MirrorIndexHandler(BaseHandler):
	def get(self):
		ip_addr = self.get_argument("addr", None)
		if not ip_addr:
			ip_addr = self.get_remote_ip()

		location = self.geoip.get_location(ip_addr)

		# Get a list of all mirrors.
		mirrors = self.mirrors.get_all()

		# Choose the preferred ones by their location.
		preferred_mirrors = mirrors.get_for_location(location)

		self.render("mirrors.html",
			preferred_mirrors=preferred_mirrors, mirrors=mirrors)


class MirrorItemHandler(BaseHandler):
	def get(self, what):
		mirror = self.mirrors.get_by_hostname(what)
		if not mirror:
			mirror = self.mirrors.get(id)

		if not mirror:
			raise tornado.web.HTTPError(404, what)

		ip_addr = self.get_argument("addr", None)
		if not ip_addr:
			ip_addr = self.get_remote_ip()
		client_location = self.geoip.get_location(ip_addr)

		client_distance = mirror.distance_to(client_location, ignore_preference=True)

		self.render("mirrors-item.html", item=mirror, client_distance=client_distance)


class MirrorHandler(BaseHandler):
	def get(self):
		self.redirect("mirrors/all")


class MirrorAllHandler(BaseHandler):
	def get(self):
		self.render("downloads-mirrors.html", mirrors=self.mirrors.list())


class MirrorDetailHandler(BaseHandler):
	def get(self, id):
		self.render("download-mirror-detail.html", mirror=self.mirrors.get(id))


class MirrorListPakfire2Handler(BaseHandler):
	def get(self):
		suffix = self.get_argument("suffix", "")
		development = self.get_argument("development", None)

		self.set_header("Content-Type", "text/plain")

		# Get all mirror servers that are currently up.
		mirrors = self.mirrors.get_all_up()

		lines = []
		for m in mirrors:
			if not m.mirrorlist:
				continue

			# Skip all non-development mirrors
			# if we run in development mode.
			if development and not m.development:
				continue

			path = [m.path, "pakfire2"]

			if suffix:
				path.append(suffix)

			path = "/".join(path)

			# Remove double slashes.
			path = path.replace("//", "/")

			# Remove leading slash.
			if path.startswith("/"):
				path = path[1:]

			# Remove trailing slash.
			if path.endswith("/"):
				path = path[:-1]

			line = ("HTTP", m.hostname, path, "")
			lines.append(";".join(line))

		self.finish("\r\n".join(lines))
