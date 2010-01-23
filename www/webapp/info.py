#!/usr/bin/python

from helpers import json_loads

class Info(dict):
	def __init__(self, filename):
		self.load(filename)
		
	def load(self, filename):
		f = open(filename)
		for key, val in json_loads(f.read()).items():
			self[key] = val
		f.close()


info = Info("info.json")
