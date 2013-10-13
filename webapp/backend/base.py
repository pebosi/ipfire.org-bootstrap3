#!/usr/bin/python

import tornado.database

import accounts
import planet

MYSQL_SERVER = "mysql-master.ipfire.org"
MYSQL_DB     = "webapp"
MYSQL_USER   = "webapp"

class Backend(object):
	def __init__(self):
		self.db = tornado.database.Connection(MYSQL_SERVER, MYSQL_DB, user=MYSQL_USER)

		self.accounts = accounts.Accounts(self)
		self.planet = planet.Planet(self)
