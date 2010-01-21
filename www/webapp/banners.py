#!/usr/bin/python

import random
import simplejson

from helpers import Item, _stringify

class Banners(object):
	def __init__(self, filename=None):
		self.items = []

		if filename:
			self.load(filename)

	def load(self, filename):
		f = open(filename)
		data = f.read()
		f.close()
		
		for item in simplejson.loads(data):
			self.items.append(Item(**_stringify(item)))

	def get(self):
		return random.choice(self.items)


banners = Banners("banners.json")
