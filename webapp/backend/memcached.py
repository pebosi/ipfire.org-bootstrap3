#!/usr/bin/python

import memcache

from misc import Singleton
from settings import Settings

class Memcached(object):
	__metaclass__ = Singleton

	def __init__(self):
		# Fetch hosts from database
		hosts = Settings().get("memcached_servers").split(",")

		self._connection = memcache.Client(hosts, debug=0)

	def get(self, key, *args, **kwargs):
		key = str(key)

		return self._connection.get(key, *args, **kwargs)

	def set(self, key, *args, **kwargs):
		key = str(key)

		return self._connection.set(key, *args, **kwargs)

	def delete(self, key, *args, **kwargs):
		key = str(key)

		return self._connection.delete(key, *args, **kwargs)
