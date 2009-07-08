#!/usr/bin/python

import simplejson as json

class Json:
	def __init__(self, file):
		f = open(file)
		data = f.read()
		data = data.replace('\n', '') # Remove all \n
		data = data.replace('\t', ' ') # Remove all \t
		self.json = json.loads(data)
		f.close()
