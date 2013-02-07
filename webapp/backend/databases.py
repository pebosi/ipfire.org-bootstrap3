#!/usr/bin/python

import logging
import tornado.database

from misc import Singleton

class Row(tornado.database.Row):
	pass

MYSQL_SERVER = "mysql-master.ipfire.org"

class Databases(object):
	__metaclass__ = Singleton

	def __init__(self):
		self._connections = {}

	@property
	def webapp(self):
		if not self._connections.has_key("webapp"):
			self._connections["webapp"] = \
				Connection(MYSQL_SERVER, "webapp", user="webapp")

		return self._connections["webapp"]

	@property
	def geoip(self):
		if not self._connections.has_key("geoip"):
			self._connections["geoip"] = \
				Connection(MYSQL_SERVER, "geoip", user="webapp")

		return self._connections["geoip"]


class Connection(tornado.database.Connection):
	def __init__(self, *args, **kwargs):
		logging.debug("Creating new database connection: %s" % args[1])

		tornado.database.Connection.__init__(self, *args, **kwargs)

	def update(self, table, item_id, **items):
		query = "UPDATE %s SET " % table

		keys = []
		for k, v in items.items():
			# Never update id
			if k == "id":
				continue

			keys.append("%s='%s'" % (k, v))

		query += ", ".join(keys)
		query += " WHERE id=%s" % item_id

		return self.execute(query)

	def insert(self, table, **items):
		query = "INSERT INTO %s" % table

		keys = []
		vals = []

		for k, v in items.items():
			# Never insert id
			if k == "id":
				continue

			keys.append(k)
			vals.append("'%s'" % v)

		query += "(%s)"% ", ".join(keys)
		query += " VALUES(%s)" % ", ".join(vals)

		return self.execute(query)

	def _execute(self, cursor, query, parameters):
		logging.debug("Executing query: %s" % (query % parameters))

		return tornado.database.Connection._execute(self, cursor, query, parameters)
