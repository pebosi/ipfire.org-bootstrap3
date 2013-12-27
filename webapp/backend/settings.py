#!/usr/bin/python

from misc import Object

class Settings(Object):
	def init(self):
		"""
			Initialize the settings dictionary by fetching the
			entire table from the database.
		"""
		self.__settings = {}

		query = self.db.query("SELECT k, v FROM settings")

		for row in query:
			self.__settings[row.k] = row.v

	def query(self, key):
		return self.db.get("SELECT * FROM settings WHERE k=%s", key)

	def get(self, key, default=None):
		return self.__settings.get(key, default)

	def get_int(self, key, default=None):
		value = self.get(key)

		if value is None:
			return default

		try:
			return int(value)
		except (TypeError, ValueError):
			return default

	def get_float(self, key):
		value = self.get(key)

		if value is None:
			return default

		try:
			return float(value)
		except (TypeError, ValueError):
			return default

	def set(self, key, value):
		oldvalue = self.get(key)

		if value == oldvalue:
			return

		if oldvalue:
			self.db.execute("UPDATE settings SET v = %s WHERE k = %s", value, key)
		else:
			self.db.execute("INSERT INTO settings(k, v) VALUES(%s, %s)", key, value)

	def get_all(self):
		return self.__settings.copy()
