#!/usr/bin/python

import simplejson

class Info(dict):
	def __init__(self, filename):
		self.load(filename)
		
	def load(self, filename):
		f = open(filename)
		for key, val in simplejson.loads(f.read()).items():
			self[key] = val
		f.close()


info = Info("info.json")
