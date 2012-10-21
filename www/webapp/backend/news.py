#!/usr/bin/python

from databases import Databases
from misc import Singleton

class News(object):
	__metaclass__ = Singleton

	@property
	def db(self):
		return Databases().webapp

	def list(self):
		return [i.uuid for i in self.db.query("SELECT DISTINCT uuid FROM news ORDER BY date")]

	def get(self, uuid, lang="en"):
		return self.db.get("SELECT * FROM news WHERE uuid=%s AND lang=%s",
			uuid, lang)

	def get_by_slug(self, slug):
		return self.db.get("SELECT * FROM news WHERE slug=%s", slug)

	def get_latest(self, author=None, locale=None, limit=1, offset=0):
		query = "SELECT * FROM news WHERE published='Y'"

		if author:
			query += " AND author_id='%s'" % author

		if locale:
			query += " AND lang='%s'" % locale.code[:2]

		query += " ORDER BY date DESC"

		if limit:
			if offset:
				query += " LIMIT %d,%d" % (offset, limit)
			else:
				query += " LIMIT %d" % limit

		news = self.db.query(query)

		return news

	def get_by_year(self, year, locale=None):
		query = "SELECT * FROM news WHERE published = 'Y' AND YEAR(date) = %s"
		args  = [year,]

		if locale:
			query += " AND lang = %s"
			args.append(locale.code[:2])

		query += " ORDER BY date DESC"

		return self.db.query(query, *args)

	@property
	def years(self):
		years = []

		for row in self.db.query("SELECT DISTINCT YEAR(date) AS year FROM news \
				WHERE published = 'Y' ORDER BY year DESC"):
			years.append(row.year)

		return years


if __name__ == "__main__":
	n = News()

	print n.list()
	print n.get_latest()
