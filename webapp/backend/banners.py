#!/usr/bin/python

from databases import Databases
from misc import Singleton

class Banners(object):
	__metaclass__ = Singleton

	@property
	def db(self):
		return Databases().webapp

	def list(self):
		return self.db.query("SELECT * FROM banners")

	def get_random(self):
		return self.db.get("SELECT * FROM banners ORDER BY RAND() LIMIT 1")


if __name__ == "__main__":
	b = Banners()

	print b.list()

	print "--- RANDOM ---"

	for i in range(5):
		print i, b.get_random()
