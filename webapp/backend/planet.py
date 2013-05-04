#!/usr/bin/python

import re
import textile
import tornado.database
import unicodedata

from accounts import Accounts
from databases import Databases

from misc import Singleton

class PlanetEntry(object):
	def __init__(self, entry=None):
		if entry:
			self.__entry = entry
		else:
			self.__entry = tornado.database.Row({
				"id" : None,
				"title" : "",
				"markdown" : "",
			})

	def set(self, key, val):
		self.__entry[key] = val

	@property
	def planet(self):
		return Planet()

	@property
	def id(self):
		return self.__entry.id

	@property
	def slug(self):
		return self.__entry.slug

	@property
	def title(self):
		return self.__entry.title

	@property
	def published(self):
		return self.__entry.published

	@property
	def year(self):
		return self.published.year

	@property
	def month(self):
		return self.published.month

	@property
	def updated(self):
		return self.__entry.updated

	@property
	def markdown(self):
		return self.__entry.markdown

	@property
	def abstract(self):
		return self.render(self.markdown, 400)

	def render(self, text, limit=0):
		return self.planet.render(text, limit)

	@property
	def text(self):
		return self.render(self.markdown)

	@property
	def author(self):
		return Accounts().search(self.__entry.author_id)


class Planet(object):
	__metaclass__ = Singleton

	@property
	def db(self):
		return Databases().webapp

	def get_authors(self):
		authors = []
		for author in self.db.query("SELECT DISTINCT author_id FROM planet"):
			author = Accounts().search(author.author_id)
			if author:
				authors.append(author)

		return sorted(authors)

	def get_years(self):
		res = self.db.query("SELECT DISTINCT YEAR(published) AS year \
			FROM planet ORDER BY year DESC")

		return [row.year for row in res]

	def get_entry_by_slug(self, slug):
		entry = self.db.get("SELECT * FROM planet WHERE slug = %s", slug)
		if entry:
			return PlanetEntry(entry)

	def get_entry_by_id(self, id):
		entry = self.db.get("SELECT * FROM planet WHERE id = %s", id)
		if entry:
			return PlanetEntry(entry)

	def _limit_and_offset_query(self, limit=None, offset=None):
		query = " "

		if limit:
			if offset:
				query += "LIMIT %d,%d" % (offset, limit)
			else:
				query += "LIMIT %d" % limit

		return query

	def get_entries(self, limit=3, offset=None):
		query = "SELECT * FROM planet WHERE acknowledged='Y' ORDER BY published DESC"

		# Respect limit and offset		
		query += self._limit_and_offset_query(limit=limit, offset=offset)

		entries = []
		for entry in self.db.query(query):
			entries.append(PlanetEntry(entry))

		return entries

	def get_entries_by_author(self, author_id, limit=None, offset=None):
		query = "SELECT * FROM planet WHERE author_id = '%s'" % author_id
		query += " AND acknowledged='Y' ORDER BY published DESC"

		# Respect limit and offset		
		query += self._limit_and_offset_query(limit=limit, offset=offset)

		entries = self.db.query(query)

		return [PlanetEntry(e) for e in entries]

	def get_entries_by_year(self, year):
		entries = self.db.query("SELECT * FROM planet \
			WHERE YEAR(published) = %s ORDER BY published DESC", year)

		return [PlanetEntry(e) for e in entries]

	def render(self, text, limit=0):
		if limit and len(text) >= limit:
			text = text[:limit] + "..."
		return textile.textile(text)

	def _generate_slug(self, title):
		slug = unicodedata.normalize("NFKD", title).encode("ascii", "ignore")
		slug = re.sub(r"[^\w]+", " ", slug)
		slug = "-".join(slug.lower().strip().split())

		if not slug:
			slug = "entry"

		while True:
			e = self.db.get("SELECT * FROM planet WHERE slug = %s", slug)
			if not e:
				break
			slug += "-"

		return slug

	def update_entry(self, entry):
		self.db.execute("UPDATE planet SET title = %s, markdown = %s WHERE id = %s",
			entry.title, entry.markdown, entry.id)

	def save_entry(self, entry):
		slug = self._generate_slug(entry.title)

		self.db.execute("INSERT INTO planet(author_id, title, slug, markdown, published) "
			"VALUES(%s, %s, %s, %s, UTC_TIMESTAMP())", entry.author.uid, entry.title,
			slug, entry.markdown)

	def search(self, what):
		entries = self.db.query("SELECT *, MATCH(markdown, title) AGAINST(%s) AS score \
			FROM planet WHERE MATCH(markdown, title) AGAINST(%s) ORDER BY score DESC", what, what)

		return [PlanetEntry(e) for e in entries]
