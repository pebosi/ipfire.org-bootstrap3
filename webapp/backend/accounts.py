#!/usr/bin/python
# encoding: utf-8

import hashlib
import ldap
import logging
import urllib

from misc import Singleton
from settings import Settings

class Accounts(object):
	__metaclass__ = Singleton

	@property
	def settings(self):
		return Settings()

	def __init__(self):
		self.__db = None

		self._init()

	@property
	def search_base(self):
		return Settings().get("ldap_search_base")

	@property
	def db(self):
		if not self.__db:
			ldap_uri = self.settings.get("ldap_uri")

			self.__db = ldap.initialize(ldap_uri)
			
			bind_dn = self.settings.get("ldap_bind_dn")

			if bind_dn:
				bind_pw = self.settings.get("ldap_bind_pw")

				self.__db.simple_bind(bind_dn, bind_pw)

		return self.__db

	def get(self, dn):
		return self._accounts[dn]

	def _init(self):
		self._accounts = {}
		results = self.db.search_s(self.search_base, ldap.SCOPE_SUBTREE,
			"(objectClass=posixAccount)", ["loginShell"])

		for dn, attrs in results:
			#if attrs["loginShell"] == ["/bin/bash"]:
			self._accounts[dn] = Account(dn)

	def list(self):
		return sorted(self._accounts.values())

	def find(self, uid):
		for account in self.list():
			if account.uid == uid:
				return account

	def delete(self, uid):
		account = self.find(uid)
		# XXX

	search = find


class Account(object):
	def __init__(self, dn):
		self.dn = dn

		self.__attributes = {}

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.dn)

	def __cmp__(self, other):
		return cmp(self.cn, other.cn)

	@property
	def db(self):
		return Accounts().db

	@property
	def attributes(self):
		if not self.__attributes:
			self.fetch_attributes()

		return self.__attributes

	def fetch_attributes(self):
		result = self.db.search_ext_s(self.dn, ldap.SCOPE_SUBTREE, sizelimit=1)
		dn, self.__attributes = result[0]

	def get(self, key):
		try:
			attribute = self.attributes[key]
		except KeyError:
			raise AttributeError(key)

		if len(attribute) == 1:
			return attribute[0]

		return attribute

	__getattr__ = get

	def set(self, key, value):
		mod_op = ldap.MOD_ADD
		if self.attributes.has_key(key):
			mod_op = ldap.MOD_REPLACE

		self._modify(mod_op, key, value)

	def _modify(self, op, key, value):
		modlist = [(op, key, value)]

		self.db.modify_s(self.dn, modlist)

		# Update local cache of attributes
		self.fetch_attributes()

	def delete(self, key, value=None):
		self._modify(ldap.MOD_DELETE, key, value)

	def check_password(self, password):
		"""
			Bind to the server with given credentials and return
			true if password is corrent and false if not.

			Raises exceptions from the server on any other errors.
		"""

		logging.debug("Checking credentials for %s" % self.dn)
		try:
			self.db.simple_bind_s(self.dn, password.encode("utf-8"))
		except ldap.INVALID_CREDENTIALS:
			logging.debug("Account credentials are invalid.")
			return False

		logging.debug("Successfully authenticated.")
		return True

	@property
	def is_admin(self):
		return True # XXX todo

	@property
	def email(self):
		name = self.cn.lower()
		name = name.replace(" ", ".")
		name = name.replace("Ä", "Ae")
		name = name.replace("Ö", "Oe")
		name = name.replace("Ü", "Ue")
		name = name.replace("ä", "ae")
		name = name.replace("ö", "oe")
		name = name.replace("ü", "ue")

		for mail in self.mail:
			if mail.startswith("%s@ipfire.org" % name):
				return mail

		raise Exception, "Cannot figure out email address"

	def gravatar_icon(self, size=128):
		# construct the url
		gravatar_url = "http://www.gravatar.com/avatar/" + \
			hashlib.md5(self.email.lower()).hexdigest() + "?"	
		gravatar_url += urllib.urlencode({'d': "mm", 's': str(size)})

		return gravatar_url


if __name__ == "__main__":
	a = Accounts()

	print a.list()
