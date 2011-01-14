#!/usr/bin/python

from databases import Databases
from misc import Singleton

class Settings(object):
	__metaclass__ = Singleton

	@property
	def db(self):
		return Databases().webapp

	def query(self, key):
		return self.db.get("SELECT * FROM settings WHERE k=%s", key)

	def get(self, key):
		return "%s" % self.query(key)["v"]

	def get_id(self, key):
		return self.query(key)["id"]

	def get_int(self, key):
		value = self.get(key)

		if value is None:
			return None

		return int(value)

	def get_float(self, key):
		value = self.get(key)

		if value is None:
			return None

		return float(value)

	def set(self, key, value):
		id = self.get(key)

		if not id:
			self.db.execute("INSERT INTO settings(k, v) VALUES(%s, %s)", key, value)
		else:
			self.db.execute("UPDATE settings SET v=%s WHERE id=%s" % (value, id))

	def get_all(self):
		attrs = {}

		for s in self.db.query("SELECT * FROM settings"):
			attrs[s.k] = s.v

		return attrs


if __name__ == "__main__":
	s = Settings()

	print s.get_all()
