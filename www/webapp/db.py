#!/usr/bin/python

import hashlib
import sqlite3
import os.path


class HashDatabase(object):
	def __init__(self):
		self.conn = sqlite3.connect("/srv/www/ipfire.org/source/hashes.db")
		self.conn.isolation_level = None # autocommit mode

		self.prepare()

	def __del__(self):
		self.conn.close()

	def prepare(self):
		c = self.conn.cursor()
		c.execute("CREATE TABLE IF NOT EXISTS hashes(file, sha1)")
		c.close()

	def _save_hash(self, path, hash):
		c = self.conn.cursor()
		c.execute("INSERT INTO hashes VALUES('%s', '%s')" % (os.path.basename(path), hash))
		c.close()

	def get_hash(self, path):
		c = self.conn.cursor()
		c.execute("SELECT sha1 FROM hashes WHERE file = '%s'" % os.path.basename(path))

		hash = c.fetchone()
		c.close()

		if not hash:
			hash = self._calc_hash(path)
			self._save_hash(path, hash)

		if hash:
			return "%s" % hash

	def _calc_hash(self, path):
		if not os.path.exists(path):
			return

		m = hashlib.sha1()
		f = open(path)
		m.update(f.read())
		f.close()

		return m.hexdigest()
