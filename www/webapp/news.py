#!/usr/bin/python

from helpers import Item, _stringify, json_loads

class News(object):
	def __init__(self, filename=None):
		self.items = []

		if filename:
			self.load(filename)

	def load(self, filename):
		f = open(filename)
		data = f.read()
		f.close()

		data = data.replace("\n", "").replace("\t", " ")

		json = json_loads(data)
		for key in sorted(json.keys()):
			self.items.append(NewsItem(**_stringify(json[key])))

	def get(self, limit=None):
		ret = self.items[:]
		ret.reverse()
		if limit:
			ret = ret[:limit]
		return ret


NewsItem = Item

news = News("news.json")
