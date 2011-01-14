#!/usr/bin/python

import textile
import tornado.database

import backend

from handlers_base import *

class RSSHandler(BaseHandler):
	_cache_prefix = ""

	@property
	def cache_prefix(self):
		return self._cache_prefix

	def prepare(self):
		self.set_header("Content-Type", "application/rss+xml")

	def get(self):
		offset = int(self.get_argument("offset", 0))
		limit = int(self.get_argument("limit", 10))

		rss_id = "rss-%s-locale=%s-limit=%s-offset=%s" % \
			(self.cache_prefix, self.locale.code, limit, offset)

		items = self.memcached.get(rss_id)
		if not items:
			items = self.generate()
			
			self.memcached.set(rss_id, items, 15)

		self.render("rss.xml", items=items, title=self.title,
			url=self.url, description=self.description)

	def generate(self):
		raise NotImplementedError


class RSSNewsHandler(RSSHandler):
	_cache_prefix = "news"

	title = "IPFire.org - News"
	url   = "http://www.ipfire.org/"
	description = "IPFire News Feed"

	def generate(self):
		offset = int(self.get_argument("offset", 0))
		limit = int(self.get_argument("limit", 10))

		news = self.news.get_latest(
			locale=self.locale,
			limit=limit,
			offset=offset,
		)

		items = []
		for n in news:
			# Get author information
			author = self.get_account(n.author_id)
			n.author = tornado.database.Row(
				name = author.cn,
				mail = author.email,
			)

			# Render text
			n.text = textile.textile(n.text)

			item = tornado.database.Row({
				"title"  : n.title,
				"author" : n.author,
				"date"   : n.date,
				"url"    : "http://www.ipfire.org/news/%s" % n.slug,
				"text"   : n.text,
			})
			items.append(item)

		return items


class RSSPlanetAllHandler(RSSHandler):
	_cache_prefix = "planet"

	title = "IPFire.org - Planet"
	url   = "http://planet.ipfire.org/"
	description = "IPFire Planet Feed"

	def generate(self):
		offset = int(self.get_argument("offset", 0))
		limit = int(self.get_argument("limit", 10))

		news = self.planet.get_entries(
			limit=limit,
			offset=offset,
		)

		items = []
		for n in news:
			# Get author information
			author = tornado.database.Row(
				name = n.author.cn,
				mail = n.author.email,
			)

			item = tornado.database.Row({
				"title"  : n.title,
				"author" : author,
				"date"   : n.published,
				"url"    : "http://planet.ipfire.org/post/%s" % n.slug,
				"text"   : textile.textile(n.text),
			})
			items.append(item)

		return items


class RSSPlanetUserHandler(RSSPlanetAllHandler):
	@property
	def cache_prefix(self):
		return "%s-user=%s" % (self._cache_prefix, self.user)

	def get(self, user):
		self.user = user

		return RSSPlanetAllHandler.get(self)

	def generate(self):
		offset = int(self.get_argument("offset", 0))
		limit = int(self.get_argument("limit", 10))

		news = self.planet.get_entries_by_author(
			self.user,
			limit=limit,
			offset=offset,
		)

		items = []
		for n in news:
			# Get author information
			author = tornado.database.Row(
				name = n.author.cn,
				mail = n.author.email,
			)

			item = tornado.database.Row({
				"title"  : n.title,
				"author" : author,
				"date"   : n.published,
				"url"    : "http://planet.ipfire.org/post/%s" % n.slug,
				"text"   : textile.textile(n.text),
			})
			items.append(item)

		return items
