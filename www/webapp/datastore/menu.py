#!/usr/bin/python

import simplejson

from tornado.database import Row

class Menu(object):
	def __init__(self, application, filename=None):
		self.application = application
		self.items = {}

		if filename:
			self.load(filename)

	def load(self, filename):
		with open(filename) as f:
			for url, items in simplejson.load(f).items():
				self.items[url] = []
				for item in items:
					self.items[url].append(Row(item))

	def get(self, url):
		return self.items.get(url, [])
