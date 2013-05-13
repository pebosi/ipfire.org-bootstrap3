#!/usr/bin/python

#import httplib
#import logging
#import markdown2
import os
#import random
#import re
#import socket
#import time
#import tornado.database
#import tornado.locale
import tornado.web
#import unicodedata

import backend

from handlers_admin import *
from handlers_base import *
from handlers_boot import *
from handlers_download import *
from handlers_iuse import *
from handlers_mirrors import *
from handlers_news import *
from handlers_nopaste import *
from handlers_planet import *
from handlers_rss import *
from handlers_stasy import *
from handlers_tracker import *
from handlers_wishlist import *

class RootHandler(BaseHandler):
	"""
		This handler redirects any request directly to /.

		It can be used to be compatible with some ancient index urls.
	"""
	def get(self, *args):
		self.redirect("/")


class LangCompatHandler(BaseHandler):
	"""
		Redirect links in the old format to current site:

		E.g. /en/index -> /index
	"""
	def get(self, lang, page):
		self.redirect("/%s" % page)


class IndexHandler(BaseHandler):
	rss_url = "/news.rss"

	"""
		This handler displays the welcome page.
	"""
	def get(self):
		# Get a list of the most recent news items and put them on the page.		
		latest_news = self.news.get_latest(limit=3, locale=self.locale)

		# Get a list of the most recent planet posts.
		planet_posts = self.planet.get_entries(limit=3)

		# Get the latest release.
		latest_release = self.releases.get_latest()

		return self.render("index.html", latest_news=latest_news,
			planet_posts=planet_posts, latest_release=latest_release)


class StaticHandler(BaseHandler):
	"""
		This handler shows the files that are in plain html format.
	"""
	@property
	def static_path(self):
		return os.path.join(self.application.settings["template_path"], "static")

	@property
	def static_files(self):
		for dir, subdirs, files in os.walk(self.static_path):
			dir = dir[len(self.static_path) + 1:]
			for file in files:
				if not file.endswith(".html"):
					continue
				yield os.path.join(dir, file)

	def get(self, name=None):
		name = "%s.html" % name

		if not name in self.static_files:
			raise tornado.web.HTTPError(404)

		self.render("static/%s" % name, lang=self.locale.code[:2])
