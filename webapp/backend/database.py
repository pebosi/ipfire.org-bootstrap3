#!/usr/bin/env python

"""
	A lightweight wrapper around psycopg2.

	Originally part of the Tornado framework.  The tornado.database module
	is slated for removal in Tornado 3.0, and it is now available separately
	as torndb.
"""

from __future__ import absolute_import, division, with_statement

import copy
import itertools
import logging
import os
import psycopg2
import time

class Connection(object):
	"""
		A lightweight wrapper around MySQLdb DB-API connections.

		The main value we provide is wrapping rows in a dict/object so that
		columns can be accessed by name. Typical usage::

			db = torndb.Connection("localhost", "mydatabase")
			for article in db.query("SELECT * FROM articles"):
				print article.title

		Cursors are hidden by the implementation, but other than that, the methods
		are very similar to the DB-API.

		We explicitly set the timezone to UTC and the character encoding to
		UTF-8 on all connections to avoid time zone and encoding errors.
	"""
	def __init__(self, host, database, user=None, password=None):
		self.host = host
		self.database = database

		self._db = None
		self._db_args = {
			"host"     : host,
			"database" : database,
			"user"     : user,
			"password" : password,
		}

		try:
			self.reconnect()
		except Exception:
			logging.error("Cannot connect to database on %s", self.host, exc_info=True)

	def __del__(self):
		self.close()

	def close(self):
		"""
			Closes this database connection.
		"""
		if getattr(self, "_db", None) is not None:
			self._db.close()
			self._db = None

	def reconnect(self):
		"""
			Closes the existing database connection and re-opens it.
		"""
		self.close()

		self._db = psycopg2.connect(**self._db_args)
		self._db.autocommit = True

		# Initialize the timezone setting.
		self.execute("SET TIMEZONE TO 'UTC'")

	def query(self, query, *parameters, **kwparameters):
		"""
			Returns a row list for the given query and parameters.
		"""
		cursor = self._cursor()
		try:
			self._execute(cursor, query, parameters, kwparameters)
			column_names = [d[0] for d in cursor.description]
			return [Row(itertools.izip(column_names, row)) for row in cursor]
		finally:
			cursor.close()

	def get(self, query, *parameters, **kwparameters):
		"""
			Returns the first row returned for the given query.
		"""
		rows = self.query(query, *parameters, **kwparameters)
		if not rows:
			return None
		elif len(rows) > 1:
			raise Exception("Multiple rows returned for Database.get() query")
		else:
			return rows[0]

	def execute(self, query, *parameters, **kwparameters):
		"""
			Executes the given query, returning the lastrowid from the query.
		"""
		return self.execute_lastrowid(query, *parameters, **kwparameters)

	def execute_lastrowid(self, query, *parameters, **kwparameters):
		"""
			Executes the given query, returning the lastrowid from the query.
		"""
		cursor = self._cursor()
		try:
			self._execute(cursor, query, parameters, kwparameters)
			return cursor.lastrowid
		finally:
			cursor.close()

	def execute_rowcount(self, query, *parameters, **kwparameters):
		"""
			Executes the given query, returning the rowcount from the query.
		"""
		cursor = self._cursor()
		try:
			self._execute(cursor, query, parameters, kwparameters)
			return cursor.rowcount
		finally:
			cursor.close()

	def executemany(self, query, parameters):
		"""
			Executes the given query against all the given param sequences.

			We return the lastrowid from the query.
		"""
		return self.executemany_lastrowid(query, parameters)

	def executemany_lastrowid(self, query, parameters):
		"""
			Executes the given query against all the given param sequences.

			We return the lastrowid from the query.
		"""
		cursor = self._cursor()
		try:
			cursor.executemany(query, parameters)
			return cursor.lastrowid
		finally:
			cursor.close()

	def executemany_rowcount(self, query, parameters):
		"""
			Executes the given query against all the given param sequences.

			We return the rowcount from the query.
		"""
		cursor = self._cursor()

		try:
			cursor.executemany(query, parameters)
			return cursor.rowcount
		finally:
			cursor.close()

	def _ensure_connected(self):
		if self._db is None:
			self.reconnect()

	def _cursor(self):
		self._ensure_connected()
		return self._db.cursor()

	def _execute(self, cursor, query, parameters, kwparameters):
		try:
			return cursor.execute(query, kwparameters or parameters)
		except OperationalError:
			logging.error("Error connecting to database on %s", self.host)
			self.close()
			raise


class Row(dict):
	"""A dict that allows for object-like property access syntax."""
	def __getattr__(self, name):
		try:
			return self[name]
		except KeyError:
			raise AttributeError(name)


# Alias some common exceptions
IntegrityError = psycopg2.IntegrityError
OperationalError = psycopg2.OperationalError
