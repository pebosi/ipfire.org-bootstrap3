#!/usr/bin/python

import logging
import memcache

from misc import Object

class Memcached(Object):
	def init(self):
		self._connection = None

		servers = self.get_servers()

		# Nothing to do, if no servers have been configured.
		if not servers:
			logging.warning("No memcache servers defined")
			return

		logging.info("Using memcache servers: %s" % ", ".join(servers))
		self._connection = memcache.Client(servers, debug=0)

	def get_servers(self):
		servers = self.settings.get("memcached_servers")

		if servers:
			return servers.split(" ")

	def get(self, key, *args, **kwargs):
		if not self._connection:
			return

		key = str(key)

		return self._connection.get(key, *args, **kwargs)

	def set(self, key, *args, **kwargs):
		if not self._connection:
			return

		key = str(key)

		return self._connection.set(key, *args, **kwargs)

	def delete(self, key, *args, **kwargs):
		if not self._connection:
			return

		key = str(key)

		return self._connection.delete(key, *args, **kwargs)
