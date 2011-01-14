#!/usr/bin/python

import logging
import os.path
import socket
import time
import tornado.httpclient

from databases import Databases
from geoip import GeoIP
from misc import Singleton

class Mirrors(object):
	__metaclass__ = Singleton

	@property
	def db(self):
		return Databases().webapp

	def list(self):
		return [Mirror(m.id) for m in self.db.query("SELECT id FROM mirrors ORDER BY state")]

	def check_all(self):
		for mirror in self.list():
			mirror.check()

	def get(self, id):
		return Mirror(id)

	def get_by_hostname(self, hostname):
		mirror = self.db.get("SELECT id FROM mirrors WHERE hostname=%s", hostname)

		return Mirror(mirror.id)

	def get_with_file(self, filename, country=None):
		# XXX quick and dirty solution - needs a performance boost
		mirror_ids = [m.mirror for m in self.db.query("SELECT mirror FROM mirror_files WHERE filename=%s", filename)]

		#if country:
		#	# Sort out all mirrors that are not preferred to the given country
		#	for mirror in self.get_for_country(country):
		#		if not mirror.id in mirror_ids:
		#			mirror_ids.remove(mirror.id)

		mirrors = []
		for mirror_id in mirror_ids:
			mirror = self.get(mirror_id)
			if not mirror.state == "UP":
				continue
			mirrors.append(mirror)

		logging.debug("%s" % mirrors)

		return mirrors

	def get_for_country(self, country):
		# XXX need option for random order
		mirrors = self.db.query("SELECT id FROM mirrors WHERE prefer_for_countries LIKE %s", country)

		for mirror in mirrors:
			yield self.get(mirror.id)

	def get_all_files(self):
		files = []

		for mirror in self.list():
			if not mirror.state == "UP":
				continue

			for file in mirror.filelist:
				if not file in files:
					files.append(file)

		return files


class Mirror(object):
	def __init__(self, id):
		self.id = id

		self.reload()

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.url)

	def __cmp__(self, other):
		return cmp(self.id, other.id)

	@property
	def db(self):
		return Databases().webapp

	def reload(self):
		self._info = self.db.get("SELECT * FROM mirrors WHERE id=%s", self.id)
		self._info["url"] = self.generate_url()

	def generate_url(self):
		url = "http://%s" % self.hostname
		if not self.path.startswith("/"):
			url += "/"
		url += "%s" % self.path
		if not self.path.endswith("/"):
			url += "/"
		return url

	def __getattr__(self, key):
		try:
			return self._info[key]
		except KeyError:
			raise AttributeError(key)

	@property
	def address(self):
		return socket.gethostbyname(self.hostname)

	@property
	def country_code(self):
		return GeoIP().get_country(self.address).lower() or "unknown"

	@property
	def filelist(self):
		filelist = self.db.query("SELECT filename FROM mirror_files WHERE mirror=%s ORDER BY filename", self.id)
		return [f.filename for f in filelist]

	@property
	def prefix(self):
		if self.type.startswith("pakfire"):
			return self.type

		return ""

	def set_state(self, state):
		logging.info("Setting state of %s to %s" % (self.hostname, state))

		if self.state == state:
			return

		self.db.execute("UPDATE mirrors SET state=%s WHERE id=%s",
			state, self.id)

		# Reload changed settings
		self.reload()

	def check(self):
		logging.info("Running check for mirror %s" % self.hostname)

		self.check_timestamp()
		self.check_filelist()

	def check_state(self):
		logging.debug("Checking state of mirror %s" % self.id)

		if self.disabled == "Y":
			self.set_state("DOWN")

		time_diff = time.time() - self.last_update
		if time_diff > 3*24*60*60: # XXX get this into Settings
			self.set_state("DOWN")
		elif time_diff > 6*60*60:
			self.set_state("OUTOFSYNC")
		else:
			self.set_state("UP")

	def check_timestamp(self):
		if self.releases == "N":
			return

		http = tornado.httpclient.AsyncHTTPClient()

		http.fetch(self.url + ".timestamp",
			headers={ "Pragma" : "no-cache" },
			callback=self.__check_timestamp_response)

	def __check_timestamp_response(self, response):
		if response.error:
			logging.debug("Error getting timestamp from %s" % self.hostname)
			return

		try:
			timestamp = int(response.body.strip())
		except ValueError:
			timestamp = 0

		self.db.execute("UPDATE mirrors SET last_update=%s WHERE id=%s",
			timestamp, self.id)

		# Reload changed settings
		self.reload()

		self.check_state()

		logging.info("Successfully updated timestamp from %s" % self.hostname)

	def check_filelist(self):
		# XXX need to remove data from disabled mirrors
		if self.releases == "N" or self.disabled == "Y" or self.type != "full":
			return

		http = tornado.httpclient.AsyncHTTPClient()

		http.fetch(self.url + ".filelist",
			headers={ "Pragma" : "no-cache" },
			callback=self.__check_filelist_response)

	def __check_filelist_response(self, response):
		if response.error:
			logging.debug("Error getting timestamp from %s" % self.hostname)
			return

		self.db.execute("DELETE FROM mirror_files WHERE mirror=%s", self.id)

		for file in response.body.splitlines():
			self.db.execute("INSERT INTO mirror_files(mirror, filename) VALUES(%s, %s)",
					self.id, os.path.join(self.prefix, file))

		logging.info("Successfully updated mirror filelist from %s" % self.hostname)

	@property
	def prefer_for_countries(self):
		return self._info.get("prefer_for_countries", "").split()



if __name__ == "__main__":
	m = Mirrors()

	for mirror in m.list():
		print mirror.hostname, mirror.country_code
