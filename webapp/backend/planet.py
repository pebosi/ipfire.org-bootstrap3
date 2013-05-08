#!/usr/bin/python

import re
import textile
import tornado.database
import unicodedata

from accounts import Accounts
from databases import Databases

from misc import Singleton

class PlanetEntry(object):
	def __init__(self, db, entry=None):
		self.db = db

		if entry:
			self.__entry = entry
		else:
			self.__entry = tornado.database.Row({
				"id" : None,
				"title" : "",
				"markdown" : "",
				"tags" : [],
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

	# Tags

	def get_tags(self):
		if not hasattr(self, "__tags"):
			res = self.db.query("SELECT tag FROM planet_tags \
				WHERE post_id = %s ORDER BY tag", self.id)
			self.__tags = []
			for row in res:
				self.__tags.append(row.tag)

		return self.__tags

	def set_tags(self, tags):
		# Delete all existing tags.
		self.db.execute("DELETE FROM planet_tags WHERE post_id = %s", self.id)

		self.db.executemany("INSERT INTO planet_tags(post_id, tag) VALUES(%s, %s)",
			((self.id, tag) for tag in tags))

		# Update cache.
		self.__tags = tags
		self.__tags.sort()

	tags = property(get_tags, set_tags)


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
			return PlanetEntry(self.db, entry)

	def get_entry_by_id(self, id):
		entry = self.db.get("SELECT * FROM planet WHERE id = %s", id)
		if entry:
			return PlanetEntry(self.db, entry)

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
			entries.append(PlanetEntry(self.db, entry))

		return entries

	def get_entries_by_author(self, author_id, limit=None, offset=None):
		query = "SELECT * FROM planet WHERE author_id = '%s'" % author_id
		query += " AND acknowledged='Y' ORDER BY published DESC"

		# Respect limit and offset		
		query += self._limit_and_offset_query(limit=limit, offset=offset)

		entries = self.db.query(query)

		return [PlanetEntry(self.db, e) for e in entries]

	def get_entries_by_year(self, year):
		entries = self.db.query("SELECT * FROM planet \
			WHERE YEAR(published) = %s ORDER BY published DESC", year)

		return [PlanetEntry(self.db, e) for e in entries]

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

		id = self.db.execute("INSERT INTO planet(author_id, title, slug, markdown, published) "
			"VALUES(%s, %s, %s, %s, UTC_TIMESTAMP())", entry.author.uid, entry.title,
			slug, entry.markdown)

		return id

	def search(self, what):
		# Split tags.
		tags = what.split()

		query = "SELECT planet.* FROM planet INNER JOIN ( \
				SELECT post_id FROM planet_tags \
				INNER JOIN planet ON planet_tags.post_id = planet.id \
				WHERE %s GROUP BY post_id HAVING COUNT(post_id) = %%s \
			) pt ON planet.id = pt.post_id ORDER BY published DESC"

		args = (tags, len(tags))

		clauses, args = [], tags
		for tag in tags:
			clauses.append("planet_tags.tag = %s")
		args.append(len(tags))

		entries = self.db.query(query % " OR ".join(clauses), *args)
		return [PlanetEntry(self.db, e) for e in entries]

	def search_autocomplete(self, what):
		tags = what.split()
		last_tag = tags.pop()

		res = self.db.query("SELECT tag, COUNT(tag) AS count FROM planet_tags \
			WHERE tag LIKE %s GROUP BY tag ORDER BY count DESC", "%s%%" % last_tag)

		if tags:
			return ["%s %s" % (" ".join(tags), row.tag) for row in res]

		return [row.tag for row in res]
