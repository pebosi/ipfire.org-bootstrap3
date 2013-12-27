#!/usr/bin/python

import logging
import random
import tornado.web

import backend

from handlers_base import *

class DownloadsIndexHandler(BaseHandler):
	def get(self):
		releases = self.releases.get_all()

		self.render("downloads-index.html", releases=releases)


class DownloadsReleaseHandler(BaseHandler):
	def get(self, release):
		release = self.releases.get_by_sname(release)

		if not release:
			release = self.releases.get_by_id(release)

		if not release:
			raise tornado.web.HTTPError(404)

		self.render("downloads-item.html", release=release, latest=False)


class DownloadsLatestHandler(BaseHandler):
	def get(self):
		release = self.releases.get_latest()
		if not release:
			raise tornado.web.HTTPError(404)

		self.render("downloads-item.html", release=release, latest=True)


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
	def prepare(self):
		self.set_header("Pragma", "no-cache")

	def head(self, filename):
		self.redirect_to_mirror(filename)

	def get(self, filename):
		self.redirect_to_mirror(filename, log_download=True)

	def find_mirror(self, filename):
		# Get all mirrors...
		mirrors = self.mirrors.get_all()
		mirrors = mirrors.get_with_file(filename)
		mirrors = mirrors.get_with_state("UP")

		if not mirrors:
			raise tornado.web.HTTPError(404, "File not found: %s" % filename)

		# Find mirrors located near to the user.
		# If we have not found any, we use all.
		remote_location = self.get_remote_location()

		if remote_location:
			mirrors_nearby = mirrors.get_for_location(remote_location)

			if mirrors_nearby:
				mirrors = mirrors_nearby

		return mirrors.get_random()

	def redirect_to_mirror(self, filename, log_download=False):
		# Find a random mirror.
		mirror = self.find_mirror(filename)

		# Construct the redirection URL.
		download_url = mirror.build_url(filename)

		# Redirect the request.
		self.redirect(download_url)

		if not log_download:
			return

		remote_location = self.get_remote_location()
		if remote_location:
			country_code = remote_location.country
		else:
			country_code = None

		self.db.execute("INSERT INTO log_download(filename, mirror, country_code) \
			VALUES(%s, %s, %s)", filename, mirror.id, country_code)


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


class DownloadSplashHandler(BaseHandler):
	def get(self):
		self.render("download-splash.html")
