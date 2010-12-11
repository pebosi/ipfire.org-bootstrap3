#!/usr/bin/python

import random

import tornado.web

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
		mirrors = self.mirrors.get_with_file(filename)

		# Choose a random one
		# XXX need better metric here
		mirror = random.choice(mirrors)

		self.redirect(mirror.url + filename)
