#!/usr/bin/python

from __future__ import division

import httplib
import datetime
import time
import tornado.locale
import tornado.web

import backend

def format_size(b):
	units = ["B", "k", "M", "G"]
	unit_pointer = 0

	while b >= 1024 and unit_pointer < len(units):
		b /= 1024
		unit_pointer += 1

	return "%.1f%s" % (b, units[unit_pointer])


class BaseHandler(tornado.web.RequestHandler):
	rss_url = None

	def get_account(self, uid):
		# Find the name of the author
		return self.accounts.find(uid)

	def get_query_locale(self):
		locale = self.get_argument("locale", None)

		if locale is None:
			return

		return tornado.locale.get(locale)

	def prepare(self):
		locale = self.get_query_locale()
		if locale:
			self.set_cookie("locale", locale.code)

	def get_user_locale(self):
		# The planet is always in english.
		if self.request.host == "planet.ipfire.org":
			return tornado.locale.get("en_US")

		# Get the locale from the query.
		locale = self.get_query_locale()
		if locale:
			return locale

		# Read the locale from the cookies.
		locale = self.get_cookie("locale", None)
		if locale:
			return tornado.locale.get(locale)

		# Otherwise take the browser locale.
		return self.get_browser_locale()

	@property
	def render_args(self):
		today = datetime.date.today()

		return {
			"format_size" : format_size,
			"hostname" : self.request.host,
			"lang" : self.locale.code[:2],
			"rss_url" : self.rss_url,
			"year" : today.year,
		}

	def render(self, *args, **_kwargs):
		kwargs = self.render_args
		kwargs.update(_kwargs)
		tornado.web.RequestHandler.render(self, *args, **kwargs)

	def render_string(self, *args, **_kwargs):
		kwargs = self.render_args
		kwargs.update(_kwargs)
		return tornado.web.RequestHandler.render_string(self, *args, **kwargs)

	def write_error(self, status_code, **kwargs):
		if status_code in (404, 500):
			render_args = ({
				"code"      : status_code,
				"exception" : kwargs.get("exception", None),
				"message"   : httplib.responses[status_code],
			})
			self.render("error-%s.html" % status_code, **render_args)
		else:
			return tornado.web.RequestHandler.write_error(self, status_code, **kwargs)

	def static_url(self, path, static=True):
		ret = tornado.web.RequestHandler.static_url(self, path)

		if self.settings.get("debug", False):
			return ret

		if static:
			return "http://static.ipfire.org%s" % ret

		return ret

	@property
	def backend(self):
		return self.application.backend

	@property
	def advertisements(self):
		return backend.Advertisements()

	@property
	def accounts(self):
		return self.backend.accounts

	@property
	def banners(self):
		return backend.Banners()

	@property
	def memcached(self):
		return backend.Memcached()

	@property
	def mirrors(self):
		return backend.Mirrors()

	@property
	def news(self):
		return backend.News()

	@property
	def config(self):
		return backend.Config()

	@property
	def releases(self):
		return backend.Releases()

	@property
	def banners(self):
		return backend.Banners()

	@property
	def geoip(self):
		return backend.GeoIP()

	@property
	def tracker(self):
		return backend.Tracker()

	@property
	def planet(self):
		return self.backend.planet

	@property
	def wishlist(self):
		return backend.Wishlist()
