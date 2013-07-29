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
		wish = self.db.get("SELECT * FROM wishlist WHERE slug = %s", slug)

		if wish:
			return Wish(self, wish.id)

	def get_all_by_query(self, query, *args):
		wishes = []

		for row in self.db.query(query, *args):
			wish = Wish(self, row.id, row)
			wishes.append(wish)

		return wishes

	def get_all_running(self):
		return self.get_all_by_query("SELECT * FROM wishlist \
			WHERE DATE(NOW()) >= date_start AND DATE(NOW()) <= date_end AND status = 'running' \
			ORDER BY prio ASC, date_end ASC")

	def get_all_finished(self, limit=5, offset=None):
		query = "SELECT * FROM wishlist WHERE DATE(NOW()) > date_end AND status IS NOT NULL \
			ORDER BY date_end DESC"
		args = []

		if limit:
			if offset:
				query += " LIMIT %s,%s"
				args += [limit, offset]
			else:
				query += " LIMIT %s"
				args.append(limit)

		return self.get_all_by_query(query, *args)

	def get_hot_wishes(self, limit=3):
		query = "SELECT * FROM wishlist \
			WHERE status = %s AND DATE(NOW()) BETWEEN date_start AND date_end AND ( \
				((UNIX_TIMESTAMP() - UNIX_TIMESTAMP(date_start)) <= 864000) \
				OR ((UNIX_TIMESTAMP(date_end) - UNIX_TIMESTAMP()) <= 1209600) \
				OR ((donated / goal) >= 0.9) \
				OR (goal >= 3000) \
				OR (prio <= 5) \
			) ORDER BY prio ASC, date_end ASC LIMIT %s"

		return self.get_all_by_query(query, "running", limit)


class Wish(object):
	def __init__(self, wishlist, id, data=None):
		self.wishlist = wishlist
		self.id = id

		self.__data = data

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.title)

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
	def title_short(self):
		if len(self.title) > 30:
			return "%s..." % self.title[:30]

		return self.title

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
	def percentage_bar(self):
		if self.percentage > 100:
			return 100

		return self.percentage

	@property
	def progressbar_colour(self):
		if self.is_new():
			return "bar-success"

		if self.percentage >= 90:
			return "bar-danger"

		return "bar-warning"

	@property
	def status(self):
		if self.data.status == "running" and not self.running:
			return "closed"

		return self.data.status

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

	def is_new(self):
		return self.running_days < 10

	def get_tweet(self, locale):
		_ = locale.translate

		t = [
			_("Checkout this crowdfunding wish from #ipfire:"),
			"http://wishlist.ipfire.org/wish/%s" % self.slug,
		]

		return " ".join(t)
