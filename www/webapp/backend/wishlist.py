#!/usr/bin/python

from __future__ import division

import datetime
import textile

from databases import Databases
from misc import Singleton

class Wishlist(object):
	__metaclass__ = Singleton

	@property
	def db(self):
		return Databases().webapp

	def get(self, slug):
		wish = self.db.get("SELECT id FROM wishlist WHERE slug = %s", slug)

		if wish:
			return Wish(self, wish.id)

	def get_all_by_query(self, query):
		wishes = []

		for row in self.db.query(query):
			wish = Wish(self, row.id)
			wishes.append(wish)

		return wishes

	def get_all_running(self):
		return self.get_all_by_query("SELECT id FROM wishlist \
			WHERE DATE(NOW()) >= date_start AND DATE(NOW()) <= date_end AND published = 'Y'\
			ORDER BY prio ASC, date_end ASC")

	def get_all_finished(self):
		return self.get_all_by_query("SELECT id FROM wishlist \
			WHERE DATE(NOW()) > date_end AND published = 'Y' ORDER BY date_end ASC")


class Wish(object):
	def __init__(self, wishlist, id):
		self.wishlist = wishlist
		self.id = id

		self.__data = None

	def __cmp__(self, other):
		return cmp(self.date_end, other.date_end)

	@property
	def db(self):
		return self.wishlist.db

	@property
	def data(self):
		if self.__data is None:
			self.__data = self.db.get("SELECT * FROM wishlist WHERE id = %s", self.id)
			assert self.__data

		return self.__data

	@property
	def title(self):
		return self.data.title

	@property
	def slug(self):
		return self.data.slug

	@property
	def tag(self):
		return self.data.tag

	@property
	def description(self):
		return textile.textile(self.data.description)

	@property
	def goal(self):
		return self.data.goal

	@property
	def donated(self):
		return self.data.donated

	@property
	def percentage(self):
		return (self.donated / self.goal) * 100

	@property
	def running(self):
		if self.remaining_days < 0:
			return False

		return True

	@property
	def date_start(self):
		return self.data.date_start

	@property
	def date_end(self):
		return self.data.date_end

	@property
	def running_days(self):
		today = datetime.datetime.today()
		today = today.date()

		running = today - self.date_start
		return running.days

	@property
	def remaining_days(self):
		today = datetime.datetime.today()
		today = today.date()

		remaining = self.date_end - today
		return remaining.days

	def get_tweet(self, locale):
		_ = locale.translate

		t = [
			_("Checkout this crowdfunding wish from #ipfire:"),
			"http://wishlist.ipfire.org/wish/%s" % self.slug,
		]

		return " ".join(t)
