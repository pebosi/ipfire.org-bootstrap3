#!/usr/bin/python

import tornado.web

from handlers_base import *

import backend

from backend.databases import Databases

class PlanetBaseHandler(BaseHandler):
	@property
	def db(self):
		return Databases().webapp

	@property
	def planet(self):
		return backend.Planet()


class PlanetMainHandler(PlanetBaseHandler):
	rss_url = "/rss"

	def get(self):
		offset = int(self.get_argument("offset", 0))
		limit = int(self.get_argument("limit", 4))

		entries = self.planet.get_entries(offset=offset, limit=limit)

		self.render("planet-main.html", entries=entries,
			authors=self.planet.get_authors(),
			offset=offset + limit, limit=limit)


class PlanetUserHandler(PlanetBaseHandler):
	def get(self, author):
		author = self.accounts.search(author)
		if not author:
			raise tornado.web.HTTPError(404, "User is unknown")

		offset = int(self.get_argument("offset", 0))
		limit = int(self.get_argument("limit", 4))

		entries = self.planet.get_entries_by_author(author.uid,
			offset=offset, limit=limit)

		self.render("planet-user.html", author=author, entries=entries,
			offset=offset + limit, limit=limit, rss_url="/user/%s/rss" % author.uid)


class PlanetPostingHandler(PlanetBaseHandler):
	def get(self, slug):
		entry = self.planet.get_entry_by_slug(slug)

		if not entry:
			raise tornado.web.HTTPError(404)

		self.render("planet-posting.html",
			author=entry.author, entry=entry)
