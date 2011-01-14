#!/usr/bin/python

import re

from databases import Databases
from misc import Singleton

class Menu(object):
	__metaclass__ = Singleton

	@property
	def db(self):
		return Databases().webapp

	def get(self, host):
		menu = []
		for m in self.db.query("SELECT * FROM menu ORDER BY prio ASC"):
			try:
				if not re.match(m.sites, host) is None:
					menu.append(m)
			except re.error:
				# Drop all exceptions that occour when matching the expressions.
				pass

		return menu
