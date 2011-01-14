#!/usr/bin/python

import logging
import random
import tornado.web

import backend

from handlers_base import *

class DownloadsIndexHandler(BaseHandler):
	def get(self):
		self.render("downloads-index.html", release=self.releases.get_latest())


class DownloadsReleaseHandler(BaseHandler):
	def get(self, release):
		release = self.releases.get_by_id(release)
		if not release:
			raise tornado.web.HTTPError(404)

		self.render("downloads-item.html", item=release)


class DownloadsLatestHandler(BaseHandler):
	def get(self):
		release = self.releases.get_latest()
		if not release:
			raise tornado.web.HTTPError(404)

		self.render("downloads-item.html", item=release)


class DownloadsOlderHandler(BaseHandler):
	def get(self):
		releases = self.releases.get_stable()

		# Drop the latest release
		if releases:
			releases = releases[1:]

		self.render("downloads-older.html", releases=releases)


class DownloadsDevelopmentHandler(BaseHandler):
	def get(self):
		releases = self.releases.get_unstable()

		self.render("downloads-development.html", releases=releases)


class DownloadHandler(BaseHandler):
	def get(self):
		self.render("downloads.html", release=self.releases.get_latest())


class DownloadAllHandler(BaseHandler):
	def get(self):
		self.render("downloads-all.html",
			releases=self.releases.get_stable())


class DownloadDevelopmentHandler(BaseHandler):
	def get(self):
		self.render("downloads-development.html",
			releases=self.releases.get_unstable())


class DownloadFileHandler(BaseHandler):
	def get(self, filename):
		country_code = self.geoip.get_country(self.request.remote_ip)

		self.set_header("Pragma", "no-cache")
		self.set_header("X-Mirror-Client-Country", country_code)

		mirrors = self.mirrors.get_with_file(filename, country=country_code)
		if not mirrors:
			self.mirrors.get_with_file(filename)

		if not mirrors:
			raise tornado.web.HTTPError(404, "File not found: %s" % filename)

		mirror = random.choice(mirrors)

		self.redirect(mirror.url + filename[len(mirror.prefix):])

		self.mirrors.db.execute("INSERT INTO log_download(filename, mirror, country_code) VALUES(%s, %s, %s)",
			filename, mirror.id, country_code)


class DownloadCompatHandler(BaseHandler):
	def get(self, path, url):
		_filename = None

		for filename in self.mirrors.get_all_files():
			if filename.endswith("/%s" % url):
				_filename = filename
				break

		if not _filename:
			raise tornado.web.HTTPError(404)

		self.redirect("/%s" % _filename)

