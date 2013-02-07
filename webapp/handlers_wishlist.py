#!/usr/bin/python

import tornado.web

from handlers_base import *

class WishlistIndexHandler(BaseHandler):
	def get(self):
		wishes = self.wishlist.get_all_running()

		self.render("wishlist/index.html", wishes=wishes)


class WishlistClosedHandler(BaseHandler):
	def get(self):
		limit = self.get_argument("limit", None)
		offset = self.get_argument("offset", None)

		try:
			limit = int(limit)
		except:
			limit = 5

		try:
			offset = int(offset)
		except:
			offset = 0

		wishes = self.wishlist.get_all_finished(limit=limit + 1, offset=offset)

		if len(wishes) > limit:
			wishes = wishes[:limit]
			has_next = True
		else:
			has_next = False

		if offset:
			has_previous = True
		else:
			has_previous = False

		self.render("wishlist/closed.html", wishes=wishes, limit=limit, offset=offset,
			has_next=has_next, has_previous=has_previous)


class WishlistTermsHandler(BaseHandler):
	def get(self):
		return self.render("wishlist/terms.html")


class WishHandler(BaseHandler):
	def get(self, slug):
		wish = self.wishlist.get(slug)
		if not wish:
			raise tornado.web.HTTPError(404, "Could not find wish %s" % slug)

		self.render("wishlist/wish.html", wish=wish)


class WishDonateHandler(BaseHandler):
	def get(self, slug):
		wish = self.wishlist.get(slug)
		if not wish:
			raise tornado.web.HTTPError(404, "Could not find wish %s" % slug)

		self.render("wishlist/donate.html", wish=wish)
