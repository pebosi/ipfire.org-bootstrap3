#!/usr/bin/python

class Item(object):
	def __init__(self, **args):
		self.args = args
	
	def __getattr__(self, key):
		return self.args[key]

	def __getitem__(self, key):
		return self.args[key]
		
	def __setitem__(self, key, val):
		self.args[key] = val


def size(s):
	suffixes = ["B", "K", "M", "G", "T",]
	
	idx = 0
	while s >= 1024 and idx < len(suffixes):
		s /= 1024
		idx += 1

	return "%.0f%s" % (s, suffixes[idx])
	
def _stringify(d):
	ret = {}
	for key in d.keys():
		ret[str(key)] = d[key]
	return ret
