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

	def get(self, *args, **kwargs):
		return self._connection.get(*args, **kwargs)

	def set(self, *args, **kwargs):
		return self._connection.set(*args, **kwargs)

	def delete(self, *args, **kwargs):
		return self._connection.delete(*args, **kwargs)
