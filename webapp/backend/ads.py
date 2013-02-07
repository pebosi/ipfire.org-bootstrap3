#!/usr/bin/python

from __future__ import division

import datetime
import textile

from databases import Databases
from misc import Singleton

class Advertisements(object):
	__metaclass__ = Singleton

	@property
	def db(self):
		return Databases().webapp

	def get(self, where=None):
		args = []
		query = "SELECT * FROM advertisements \
			WHERE DATE(NOW()) >= date_start AND DATE(NOW()) <= date_end AND published = 'Y'"

		if where:
			query += " AND `where` = %s"
			args.append(where)

		query += " ORDER BY RAND() LIMIT 1"

		ad = self.db.get(query, *args)
		if ad:
			return Advert(self, ad.id, ad)


class Advert(object):
	def __init__(self, advertisements, id, data=None):
		self.advertisements = advertisements
		self.id = id

		self.__data = data

	@property
	def db(self):
		return self.advertisements.db

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
