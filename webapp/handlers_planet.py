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
		years = self.planet.get_years()

		self.render("planet/index.html", entries=entries, years=years,
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

		self.render("planet/user.html", author=author, entries=entries,
			offset=offset + limit, limit=limit, rss_url="/user/%s/rss" % author.uid)


class PlanetPostingHandler(PlanetBaseHandler):
	def get(self, slug):
		entry = self.planet.get_entry_by_slug(slug)

		if not entry:
			raise tornado.web.HTTPError(404)

		self.render("planet/posting.html",
			author=entry.author, entry=entry)


class PlanetSearchHandler(PlanetBaseHandler):
	def get(self):
		query = self.get_argument("q", "")

		if query:
			entries = self.planet.search(query)
		else:
			entries = []

		self.render("planet/search.html", entries=entries, query=query)


class PlanetYearHandler(PlanetBaseHandler):
	def get(self, year):
		entries = self.planet.get_entries_by_year(year)

		months = {}
		for entry in entries:
			try:
				months[entry.month].append(entry)
			except KeyError:
				months[entry.month] = [entry]

		months = months.items()
		months.sort(reverse=True)

		self.render("planet/year.html", months=months, year=year)
