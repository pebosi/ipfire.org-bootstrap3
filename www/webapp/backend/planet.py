#!/usr/bin/python

import textile

from accounts import Accounts
from databases import Databases

from misc import Singleton

class PlanetEntry(object):
	def __init__(self, entry):
		self.__entry = entry

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
	def updated(self):
		return self.__entry.updated

	@property
	def markdown(self):
		return self.__entry.markdown

	@property
	def abstract(self):
		return self.render(self.markdown, 400)

	def render(self, text, limit=0):
		if limit and len(text) >= limit:
			text = text[:limit] + "..."
		return textile.textile(text)

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

		return authors

	def get_entry_by_slug(self, slug):
		entry = self.db.get("SELECT * FROM planet WHERE slug = %s", slug)
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
		query = "SELECT * FROM planet ORDER BY published DESC"

		# Respect limit and offset		
		query += self._limit_and_offset_query(limit=limit, offset=offset)

		entries = []
		for entry in self.db.query(query):
			entries.append(PlanetEntry(entry))

		return entries

	def get_entries_by_author(self, author_id, limit=None, offset=None):
		query = "SELECT * FROM planet WHERE author_id = '%s'" % author_id
		query += " ORDER BY published DESC"

		# Respect limit and offset		
		query += self._limit_and_offset_query(limit=limit, offset=offset)


		entries = self.db.query(query)

		return [PlanetEntry(e) for e in entries]
