#!/usr/bin/python

import simplejson

from helpers import Item

class Menu(object):
	def __init__(self, filename=None):
		self.items = []

		if filename:
			self.load(filename)

	def load(self, filename):
		f = open(filename)
		data = f.read()
		f.close()
		
		for item in simplejson.loads(data):
			self.items.append(MenuItem(**item))


class MenuItem(Item):
	def __init__(self, **args):
		Item.__init__(self, **args)
		self.active = False
		
		# Parse submenu
		if self.args.has_key("subs"):
			self.args["items"] = []
			for sub in self.args["subs"]:
				self.args["items"].append(MenuItem(**sub))
			del self.args["subs"]


if __name__ == "__main__":
	m = Menu("menu.json")
	print [i.args for i in m.items]
