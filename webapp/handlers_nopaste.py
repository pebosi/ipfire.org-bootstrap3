#!/usr/bin/python

import tornado.web

from handlers_base import *


class NopasteIndexHandler(BaseHandler):
	def get(self):
		self.render("nopaste-index.html")

	def post(self):
		pass


class NopasteEntryHandler(BaseHandler):
	def get(self, uuid):
		pass

