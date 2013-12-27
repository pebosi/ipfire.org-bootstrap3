#!/usr/bin/python

from misc import Object

class News(Object):
	def get(self, uuid, lang="en"):
		return self.db.get("SELECT * FROM news WHERE uuid = %s AND lang = %s \
			AND published IS NOT NULL AND published <= NOW()", uuid, lang)

	def get_by_slug(self, slug):
		return self.db.get("SELECT * FROM news WHERE slug = %s \
			AND published IS NOT NULL AND published <= NOW()", slug)

	def get_latest(self, author=None, locale=None, limit=1, offset=0):
		query = "SELECT * FROM news WHERE published IS NOT NULL AND published <= NOW()"
		args = []

		if author:
			query += " AND author_id = %s"
			args.append(author)

		if locale:
			query += " AND lang = %s"
			args.append(locale.code[:2])

		query += " ORDER BY published DESC"

		if limit:
			query += " LIMIT %s"
			args.append(limit)

			if offset:
				query += " OFFSET %s"
				args.append(offset)

		return self.db.query(query, *args)

	def get_by_year(self, year, locale=None):
		query = "SELECT * FROM news WHERE published IS NOT NULL AND published <= NOW() \
			AND EXTRACT(YEAR FROM published) = %s"
		args  = [year,]

		if locale:
			query += " AND lang = %s"
			args.append(locale.code[:2])

		query += " ORDER BY published DESC"

		return self.db.query(query, *args)

	@property
	def years(self):
		query = self.db.query("SELECT DISTINCT EXTRACT(YEAR FROM published)::integer AS year FROM news \
			WHERE published IS NOT NULL AND published <= NOW() ORDER BY year DESC")

		return [r.year for r in query]
