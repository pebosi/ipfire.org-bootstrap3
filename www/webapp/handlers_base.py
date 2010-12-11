#!/usr/bin/python

import httplib
import time
import tornado.locale
import tornado.web

import backend

class BaseHandler(tornado.web.RequestHandler):
	def get_account(self, uid):
		# Find the name of the author
		return self.accounts.find(uid)

	def get_user_locale(self):
		DEFAULT_LOCALE = tornado.locale.get("en_US")
		ALLOWED_LOCALES = \
			[tornado.locale.get(l) for l in tornado.locale.get_supported_locales(None)]

		# One can append "?locale=de" to mostly and URI on the site and
		# another output that guessed.
		locale = self.get_argument("locale", None)
		if locale:
			locale = tornado.locale.get(locale)
			for locale in ALLOWED_LOCALES:
				return locale

		# If no locale was provided we guess what the browser sends us
		locale = self.get_browser_locale()
		if locale in ALLOWED_LOCALES:
			return locale

		# If no one of the cases above worked we use our default locale
		return DEFAULT_LOCALE

	@property
	def render_args(self):
		return {
			"hostname" : self.request.host,
			"lang" : self.locale.code[:2],
			"year" : time.strftime("%Y"),
		}

	def render(self, *args, **kwargs):
		kwargs.update(self.render_args)
		tornado.web.RequestHandler.render(self, *args, **kwargs)

	def render_string(self, *args, **kwargs):
		kwargs.update(self.render_args)
		return tornado.web.RequestHandler.render_string(self, *args, **kwargs)

	def get_error_html(self, status_code, **kwargs):
		if status_code in (404, 500):
			render_args = ({
				"code"      : status_code,
				"exception" : kwargs.get("exception", None),
				"message"   : httplib.responses[status_code],
			})
			return self.render_string("error-%s.html" % status_code, **render_args)
		else:
			return tornado.web.RequestHandler.get_error_html(self, status_code, **kwargs)

	@property
	def accounts(self):
		return backend.Accounts()

	@property
	def banners(self):
		return backend.Banners()

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
