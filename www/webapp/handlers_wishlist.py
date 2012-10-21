#!/usr/bin/python

import tornado.web

from handlers_base import *

class WishlistIndexHandler(BaseHandler):
	def get(self):
		wishes = self.wishlist.get_all_running()

		self.render("wishlist/index.html", wishes=wishes)


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
