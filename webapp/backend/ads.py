#!/usr/bin/python

from __future__ import division

import datetime
import textile

from misc import Object

class Advertisements(Object):
	def get(self, where=None):
		query = "SELECT * FROM advertisements \
			WHERE NOW() BETWEEN date_start AND date_end AND published = %s"
		args = [True]

		if where:
			query += " AND location = %s"
			args.append(where)

		query += " ORDER BY RANDOM() LIMIT 1"

		ad = self.db.get(query, *args)
		if ad:
			return Advert(self.backend, ad.id, ad)


class Advert(Object):
	def __init__(self, backend, id, data=None):
		Object.__init__(self, backend)

		self.id = id
		self.__data = data

	@property
	def data(self):
		if self.__data is None:
			self.__data = self.db.get("SELECT * FROM advertisements WHERE id = %s", self.id)
			assert self.__data

		return self.__data

	@property
	def company(self):
		return self.data.company

	@property
	def text(self):
		return self.data.text

	@property
	def url(self):
		return self.data.url

	@property
	def who(self):
		return """<a href="%s" target="_blank">%s</a>""" % (self.url, self.text or self.company)

	def update_impressions(self):
		self.db.execute("UPDATE advertisements SET impressions = impressions + 1 WHERE id = %s", self.id)
