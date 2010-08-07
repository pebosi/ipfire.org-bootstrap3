#!/usr/bin/python

import hashlib
import ldap
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


class UserDatabase(object):
	HOST = "ldap://ldap.ipfire.org"
	BASEDN = "ou=People,dc=mcfly,dc=local"

	def __init__(self):
		self.conn = ldap.initialize(self.HOST)
		self.conn.simple_bind()

	def __del__(self):
		self.conn.unbind()

	def _find_dn_by_name(self, name):
		results = self._search(filterstr="(uid=%s)" % name)
		assert len(results) == 1
		return results[0][0]
	
	def _search(self, filterstr="(objectClass=*)", attrlist=None):
		return self.conn.search_st(self.BASEDN, ldap.SCOPE_SUBTREE,
			filterstr=filterstr, attrlist=attrlist)

	def check_password(self, name, password):
		dn = self._find_dn_by_name(name)
		conn = ldap.initialize(self.HOST)
		try:
			conn.simple_bind_s(dn, password)
			return True
		except ldap.INVALID_CREDENTIALS:
			return False
		finally:
			conn.unbind_s()

	def get_user_by_id(self, id):
		results = self._search(filterstr="(uidNumber=%s)" % id)
		assert len(results) == 1
		return User(results[0][1])

	def get_user_by_name(self, name):
		results = self._search(filterstr="(uid=%s)" % name)
		assert len(results) == 1
		return User(results[0][1])

	@property
	def users(self):
		ret = []

		for dn, attr in self._search():
			if dn == self.BASEDN or not attr:
				continue
			ret.append(User(attr))

		return sorted(ret)


class User(object):
	def __init__(self, obj):
		self.obj = obj

	def __cmp__(self, other):
		return cmp(self.realname, other.realname)

	def __repr__(self):
		return "<%s '%s'>" % (self.__class__.__name__, self.name)

	@property
	def name(self):
		return self.obj["uid"][0]

	@property
	def id(self):
		return int(self.obj["uidNumber"][0])

	@property
	def mail(self):
		#return self.obj["mail"]
		return "%s@ipfire.org" % self.name

	@property
	def realname(self):
		return self.obj["cn"][0]
