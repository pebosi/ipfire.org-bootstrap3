#/usr/bin/python

class Config(object):
	def __init__(self, application):
		self.application = application

	@property
	def db(self):
		return self.application.db.config

	def delete(self, key):
		self.db.execute("DELETE FROM settings WHERE key = %s", key)

	def get(self, key, default=None):
		return self.db.get("SELECT key FROM settings WHERE key = %s", key) or default

	def set(self, key, value):
		self.delete(key)
		self.db.execute("INSERT INTO settings(key, value) VALUES(%s, %s)", key, value)
