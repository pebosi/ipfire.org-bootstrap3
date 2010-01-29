#!/usr/bin/python

import operator
import MySQLdb as sql

allowed_items = [ "cpu_mhz", "cpu_model", "formfactor", "lang", "model",
				  "ram_mb", "storage_mb", "system", "vendor", ]

class Database(object):
	_name = "uriel"
	_table = "hosts"

	def __init__(self):
		self.connection = sql.connect(user="uriel", db=self._name)

		self._count = None

	def cursor(self):
		return self.connection.cursor()

	def table(self, item, sort=0, consolidate=0):
		c = self.cursor()
		c.execute("SELECT value FROM %s WHERE item = '%s'" % (self._table, item,))

		count = 0
		results = {}
		ret = []

		if consolidate:
			result = c.fetchone()
			while result:
				count += 1
				result = "%s" % result
	
				if results.has_key(result):
					results[result] += 1
				else:
					results[result] = 1
				
				result = c.fetchone()
	
			for i in results.items():
				ret.append(i)
	
			if sort:
				ret = sorted(ret, key=operator.itemgetter(1))
				ret.reverse()
		
		else:
			result = c.fetchone()
			while result:
				ret.append(int("%s" % result))
				result = c.fetchone()

			if sort:
				ret.sort()

			count = len(ret)

		c.close()
		return (ret, count)

	def count(self):
		if not self._count:
			c = self.cursor()
			c.execute("SELECT COUNT(DISTINCT(id)) FROM %s" % self._table)
			self._count = int("%s" % c.fetchone())
			c.close()
		return self._count

	def get(self, id, item):
		c = self.cursor()
		c.execute("SELECT value FROM %s WHERE id = '%s' AND item = '%s'" % \
			(self._table, id, item,))
		ret = c.fetchall() or None
		c.close()
		return ret

	def set(self, id, item, value):
		c = self.cursor()
		if self.get(id, item):
			c.execute("UPDATE %s SET value = '%s' WHERE id = '%s' AND item = '%s'" % \
				(self._table, value, id, item,))
		else:
			c.execute("INSERT INTO %s(id, item, value) VALUES('%s', '%s', '%s')" % \
				(self._table, id, item, value))
		c.close()
