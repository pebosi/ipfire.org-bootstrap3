#!/usr/bin/python

import re
import textile
import tornado.database
import unicodedata

from accounts import Accounts
from databases import Databases

from misc import Object

class PlanetEntry(Object):
	def __init__(self, backend, data):
		Object.__init__(self, backend)

		self.data = data

	@property
	def id(self):
		return self.data.id

	@property
	def slug(self):
		return self.data.slug

	@property
	def title(self):
		return self.data.title

	@property
	def url(self):
		return "http://planet.ipfire.org/post/%s" % self.slug

	@property
	def published(self):
		return self.data.published

	@property
	def year(self):
		return self.published.year

	@property
	def month(self):
		return self.published.month

	@property
	def updated(self):
		return self.data.updated

	@property
	def markdown(self):
		return self.data.markdown

	@property
	def markup(self):
		if self.data.markup:
			return self.data.markup

		return self.render(self.markdown)

	@property
	def abstract(self):
		return self.render(self.markdown, 400)

	def render(self, text, limit=0):
		return self.planet.render(text, limit)

	@property
	def text(self):
		# Compat for markup
		return self.markup

	@property
	def author(self):
		if not hasattr(self, "__author"):
			self.__author = self.accounts.search(self.data.author_id)

		return self.__author

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


class Planet(Object):
	def get_authors(self):
		authors = []
		for author in self.db.query("SELECT DISTINCT author_id FROM planet WHERE status = %s", "published"):
			author = self.accounts.search(author.author_id)
			if author:
				authors.append(author)

		return sorted(authors)

	def get_years(self):
		res = self.db.query("SELECT DISTINCT YEAR(published) AS year \
			FROM planet WHERE status = %s ORDER BY year DESC", "published")

		return [row.year for row in res]

	def get_entry_by_slug(self, slug):
		entry = self.db.get("SELECT * FROM planet WHERE slug = %s", slug)
		if entry:
			return PlanetEntry(self.backend, entry)

	def get_entry_by_id(self, id):
		entry = self.db.get("SELECT * FROM planet WHERE id = %s", id)
		if entry:
			return PlanetEntry(self.backend, entry)

	def _limit_and_offset_query(self, limit=None, offset=None):
		query = " "

		if limit:
			if offset:
				query += "LIMIT %d,%d" % (offset, limit)
			else:
				query += "LIMIT %d" % limit

		return query

	def get_entries(self, limit=3, offset=None, status="published", author_id=None):
		query = "SELECT * FROM planet"
		args, clauses = [], []

		if status:
			clauses.append("status = %s")
			args.append(status)

		if author_id:
			clauses.append("author_id = %s")
			args.append(author_id)

		if clauses:
			query += " WHERE %s" % " AND ".join(clauses)

		query += " ORDER BY published DESC"

		# Respect limit and offset
		if limit:
			if offset:
				query += " LIMIT %s,%s"
				args += [offset, limit,]
			else:
				query += " LIMIT %s"
				args.append(limit)

		entries = []
		for entry in self.db.query(query, *args):
			entry = PlanetEntry(self.backend, entry)
			entries.append(entry)

		return entries

	def get_entries_by_author(self, author_id, limit=None, offset=None):
		return self.get_entries(limit=limit, offset=offset, author_id=author_id)

	def get_entries_by_year(self, year):
		entries = self.db.query("SELECT * FROM planet \
			WHERE status = %s AND YEAR(published) = %s ORDER BY published DESC",
			"published", year)

		return [PlanetEntry(self.backend, e) for e in entries]

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
		return [PlanetEntry(self.backend, e) for e in entries]

	def search_autocomplete(self, what):
		tags = what.split()
		last_tag = tags.pop()

		res = self.db.query("SELECT tag, COUNT(tag) AS count FROM planet_tags \
			WHERE tag LIKE %s GROUP BY tag ORDER BY count DESC", "%s%%" % last_tag)

		if tags:
			return ["%s %s" % (" ".join(tags), row.tag) for row in res]

		return [row.tag for row in res]
