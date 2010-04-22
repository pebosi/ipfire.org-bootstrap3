#!/usr/bin/python

import random

from helpers import Item, _stringify, json_loads

class Banners(object):
	def __init__(self, filename=None):
		self.items = []

		if filename:
			self.load(filename)

	def load(self, filename):
		f = open(filename)
		data = f.read()
		f.close()
		
		for item in json_loads(data):
			self.items.append(Item(**_stringify(item)))

	def get(self):
		if self.items:
			return random.choice(self.items)


banners = Banners("banners.json")
