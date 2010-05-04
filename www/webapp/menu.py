#!/usr/bin/python

import simplejson

from helpers import Item, _stringify

class Menu(object):
	def __init__(self, filename=None):
		self.items = {}

		if filename:
			self.load(filename)

	def load(self, filename):
		f = open(filename)
		data = f.read()
		f.close()

		for url, items in simplejson.loads(data).items():
			self.items[url] = []
			for item in items:
				self.items[url].append(MenuItem(**_stringify(item)))

	def get(self, url):
		return self.items.get(url, [])


class MenuItem(Item):
	def __init__(self, **args):
		Item.__init__(self, **args)
		self.active = False
		
		# Parse submenu
		if self.args.has_key("subs"):
			self.args["items"] = []
			for sub in self.args["subs"]:
				self.args["items"].append(MenuItem(**_stringify(sub)))
			del self.args["subs"]

