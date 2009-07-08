#!/usr/bin/python

from json import Json

class Info(Json):
	def __init__(self):
		Json.__init__(self, "info.json")

	def get(self, key):
		if not self.json.has_key(key):
			raise KeyError
		return self.json[key]
	
	__getitem__ = get
