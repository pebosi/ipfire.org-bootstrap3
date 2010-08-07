#!/usr/bin/python

import simplejson

from tornado.database import Row

class News(object):
	def __init__(self, application, filename=None):
		self.application = application
		self.items = []

		if filename:
			self.load(filename)

	def load(self, filename):
		f = open(filename)
		data = f.read()
		f.close()

		data = data.replace("\n", "").replace("\t", " ")

		json = simplejson.loads(data)
		for key in sorted(json.keys()):
			json[key]["id"] = key
			self.items.append(Row(json[key]))

	def get(self, limit=None):
		ret = self.items[:]
		ret.reverse()
		if limit:
			ret = ret[:limit]
		return ret
