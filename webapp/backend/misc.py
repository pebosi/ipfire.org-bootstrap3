#!/usr/bin/python

class Object(object):
	def __init__(self, backend):
		self.backend = backend

		self.init()

	def init(self):
		"""
			Function for custom initialization.
		"""
		pass

	@property
	def db(self):
		return self.backend.db

	@property
	def accounts(self):
		return self.backend.accounts

	@property
	def downloads(self):
		return self.backend.downloads

	@property
	def geoip(self):
		return self.backend.geoip

	@property
	def iuse(self):
		return self.backend.iuse

	@property
	def memcache(self):
		return self.backend.memcache

	@property
	def planet(self):
		return self.backend.planet

	@property
	def settings(self):
		return self.backend.settings
