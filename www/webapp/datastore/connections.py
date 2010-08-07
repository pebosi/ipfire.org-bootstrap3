#!/usr/bin/python

import tornado.database

MYSQL_SERVER = "mysql.ipfire.org"

class HashConnection(tornado.database.Connection):
	def __init__(self):
		tornado.database.Connection.__init__(self, MYSQL_SERVER, "hashes", user="webapp")


class PlanetConnection(tornado.database.Connection):
	def __init__(self):
		tornado.database.Connection.__init__(self, MYSQL_SERVER, "planet", user="webapp")


class TrackerConnection(tornado.database.Connection):
	def __init__(self):
		tornado.database.Connection.__init__(self, MYSQL_SERVER, "tracker", user="webapp")
