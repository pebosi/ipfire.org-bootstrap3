#!/usr/bin/python

from helpers import json_loads

class Info(dict):
	def __init__(self, application, filename):
		self.application = application
		self.load(filename)
		
	def load(self, filename):
		f = open(filename)
		for key, val in json_loads(f.read()).items():
			self[key] = val
		f.close()
