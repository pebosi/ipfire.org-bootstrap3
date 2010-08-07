#!/usr/bin/python

import random
import simplejson

from tornado.database import Row

class Banners(object):
	def __init__(self, application, filename=None):
		self.application = application
		self.items = []

		if filename:
			self.load(filename)

	def load(self, filename):
		with open(filename) as f:
			self.items = [Row(i) for i in simplejson.load(f)]

	def get(self):
		if self.items:
			return random.choice(self.items)
