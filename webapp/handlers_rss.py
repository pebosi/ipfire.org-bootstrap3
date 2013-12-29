#!/usr/bin/python

import logging
import textile
import tornado.database

import backend

from handlers_base import *

class RSSHandler(BaseHandler):
	_default_limit = 10
	_default_offset = 0

	def prepare(self):
		self.set_header("Content-Type", "application/rss+xml")

	@property
	def limit(self):
		value = self.get_argument("limit", None)

		try:
			return int(value)
		except (TypeError, ValueError):
			return self._default_limit

	@property
	def offset(self):
		value = self.get_argument("offset", None)

		try:
			return int(value)
		except (TypeError, ValueError):
			return self._default_offset

	def get(self, *args, **kwargs):
		url = "%s%s" % (self.request.host, self.request.path)

		rss_id = "rss-%s-locale=%s-limit=%s-offset=%s" % \
			(url, self.locale.code, self.limit, self.offset)

		rss = self.memcached.get(rss_id)
		if not rss:
			logging.debug("Generating RSS feed (%s)..." % rss_id)
			rss = self.generate(*args, **kwargs)

			self.memcached.set(rss_id, rss, 900)

		self.finish(rss)

	def generate(self):
		raise NotImplementedError


class RSSNewsHandler(RSSHandler):
	def generate(self):
		news = self.news.get_latest(locale=self.locale,
			limit=self.limit, offset=self.offset)

		items = []
		for n in news:
			# Get author information
			n.author = self.get_account(n.author_id)

			# Render text
			n.text = textile.textile(n.text)

			item = tornado.database.Row({
				"title"     : n.title,
				"author"    : n.author,
				"published" : n.published,
				"url"       : "http://www.ipfire.org/news/%s" % n.slug,
				"markup"    : n.text,
			})
			items.append(item)

		return self.render_string("feeds/news.xml", items=items)


class RSSPlanetAllHandler(RSSHandler):
	def generate(self):
		items = self.planet.get_entries(limit=self.limit, offset=self.offset)

		return self.render_string("feeds/planet.xml", items=items)


class RSSPlanetUserHandler(RSSPlanetAllHandler):
	def generate(self, user):
		items = self.planet.get_entries_by_author(user,
			limit=self.limit, offset=self.offset)

		return self.render_string("feeds/planet.xml", items=items)
