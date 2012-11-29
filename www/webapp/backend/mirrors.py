#!/usr/bin/python

import logging
import math
import os.path
import random
import socket
import time
import tornado.httpclient

from databases import Databases
from geoip import GeoIP
from memcached import Memcached
from misc import Singleton

class Downloads(object):
	__metaclass__ = Singleton

	@property
	def db(self):
		return Databases().webapp

	@property
	def mirrors(self):
		return Mirrors()

	@property
	def total(self):
		ret = self.db.get("SELECT COUNT(*) AS total FROM log_download")

		return ret.total

	@property
	def today(self):
		ret = self.db.get("SELECT COUNT(*) AS today FROM log_download WHERE date >= NOW() - 1000000")

		return ret.today

	@property
	def yesterday(self):
		ret = self.db.get("SELECT COUNT(*) AS yesterday FROM log_download WHERE DATE(date) = DATE(NOW())-1")

		return ret.yesterday

	@property
	def daily_map(self):
		ret = self.db.query("SELECT DATE(date) AS date, COUNT(*) AS downloads FROM log_download"
			" WHERE DATE(date) BETWEEN DATE(NOW()) - 31 AND DATE(NOW()) GROUP BY DATE(date)")

		return ret

	def get_countries(self, duration="all"):
		query = "SELECT country_code, count(country_code) AS count FROM log_download"

		if duration == "today":
			query += " WHERE date >= NOW() - 1000000"

		query += " GROUP BY country_code ORDER BY count DESC"

		results = self.db.query(query)
		ret = {}

		count = sum([o.count for o in results])
		for res in results:
			ret[res.country_code] = float(res.count) / count

		return ret

	def get_mirror_load(self, duration="all"):
		query = "SELECT mirror, COUNT(mirror) AS count FROM log_download"

		if duration == "today":
			query += " WHERE date >= NOW() - 1000000"

		query += " GROUP BY mirror ORDER BY count DESC"

		results = self.db.query(query)
		ret = {}

		count = sum([o.count for o in results])
		for res in results:
			mirror = self.mirrors.get(res.mirror)
			ret[mirror.hostname] = float(res.count) / count

		return ret


class Mirrors(object):
	__metaclass__ = Singleton

	@property
	def db(self):
		return Databases().webapp

	@property
	def memcached(self):
		return Memcached()

	def list(self):
		return [Mirror(m.id) for m in self.db.query("SELECT id FROM mirrors WHERE disabled = 'N' ORDER BY state,hostname")]

	def check_all(self):
		for mirror in self.list():
			mirror.check()

	def get(self, id):
		return Mirror(id)

	def get_all(self):
		return MirrorSet(self.list())

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

	def get_for_location(self, addr):
		distance = 10

		mirrors = []
		all_mirrors = self.list()

		location = GeoIP().get_all(addr)
		if not location:
			return None

		while all_mirrors and len(mirrors) <= 2 and distance <= 270:
			for mirror in all_mirrors:
				if mirror.distance_to(location) <= distance:
					mirrors.append(mirror)
					all_mirrors.remove(mirror)

			distance *= 1.2

		return mirrors

	def get_all_files(self):
		files = []

		for mirror in self.list():
			if not mirror.state == "UP":
				continue

			for file in mirror.filelist:
				if not file in files:
					files.append(file)

		return files


class MirrorSet(object):
	def __init__(self, mirrors):
		self._mirrors = mirrors

	def __add__(self, other):
		mirrors = []

		for mirror in self._mirrors + other._mirrors:
			if mirror in mirrors:
				continue

			mirrors.append(mirror)

		return MirrorSet(mirrors)

	def __sub__(self, other):
		mirrors = self._mirrors[:]

		for mirror in other._mirrors:
			if mirror in mirrors:
				mirrors.remove(mirror)

		return MirrorSet(mirrors)

	def __iter__(self):
		return iter(self._mirrors)

	def __len__(self):
		return len(self._mirrors)

	def __str__(self):
		return "<MirrorSet %s>" % ", ".join([m.hostname for m in self._mirrors])

	@property
	def db(self):
		return Mirrors().db

	def get_with_file(self, filename):
		with_file = [m.mirror for m in self.db.query("SELECT mirror FROM mirror_files WHERE filename=%s", filename)]

		mirrors = []
		for mirror in self._mirrors:
			if mirror.id in with_file:
				mirrors.append(mirror)

		return MirrorSet(mirrors)

	def get_random(self):
		mirrors = []
		for mirror in self._mirrors:
			for i in range(0, mirror.priority):
				mirrors.append(mirror)

		return random.choice(mirrors)

	def get_for_country(self, country):
		mirrors = []

		for mirror in self._mirrors:
			if country in mirror.prefer_for_countries:
				mirrors.append(mirror)

		return MirrorSet(mirrors)

	def get_for_location(self, addr):
		distance = 10

		mirrors = []

		location = GeoIP().get_all(addr)
		if location:
			while len(mirrors) <= 2 and distance <= 270:
				for mirror in self._mirrors:
					if mirror in mirrors:
						continue

					if mirror.distance_to(location) <= distance:
						mirrors.append(mirror)

				distance *= 1.2

		return MirrorSet(mirrors)

	def get_with_state(self, state):
		mirrors = []

		for mirror in self._mirrors:
			if mirror.state == state:
				mirrors.append(mirror)

		return MirrorSet(mirrors)


class Mirror(object):
	def __init__(self, id):
		self.id = id

		self.reload()

		self.__location = None
		self.__country_name = None

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.url)

	def __cmp__(self, other):
		return cmp(self.id, other.id)

	@property
	def db(self):
		return Databases().webapp

	def reload(self, force=False):
		memcached = Memcached()
		mem_id = "mirror-%s" % self.id

		if force:
			memcached.delete(mem_id)

		self._info = memcached.get(mem_id)
		if not self._info:
			self._info = self.db.get("SELECT * FROM mirrors WHERE id=%s", self.id)
			self._info["url"] = self.generate_url()

			memcached.set(mem_id, self._info, 60)

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
	def location(self):
		if self.__location is None:
			self.__location = GeoIP().get_all(self.address)

		return self.__location

	@property
	def latitude(self):
		return self.location.latitude

	@property
	def longitude(self):
		return self.location.longitude

	@property
	def coordinates(self):
		return (self.latitude, self.longitude)

	@property
	def coordiante_str(self):
		coordinates = []

		for i in self.coordinates:
			coordinates.append("%s" % i)

		return ",".join(coordinates)

	@property
	def country_code(self):
		return self.location.country_code.lower() or "unknown"

	@property
	def country_name(self):
		if self.__country_name is None:
			self.__country_name = GeoIP().get_country_name(self.country_code)

		return self.__country_name

	@property
	def city(self):
		if self._info["city"]:
			return self._info["city"]

		return self.location.city

	@property
	def location_str(self):
		s = self.country_name
		if self.city:
			s = "%s, %s" % (self.city, s)

		return s

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
		self.reload(force=True)

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
			self.set_state("DOWN")
			return

		try:
			timestamp = int(response.body.strip())
		except ValueError:
			timestamp = 0

		self.db.execute("UPDATE mirrors SET last_update=%s WHERE id=%s",
			timestamp, self.id)

		# Reload changed settings
		self.reload(force=True)

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

		files = self.filelist

		for file in response.body.splitlines():
			file = os.path.join(self.prefix, file)

			if file in files:
				files.remove(file)
				continue

			self.db.execute("INSERT INTO mirror_files(mirror, filename) VALUES(%s, %s)",
				self.id, file)

		for file in files:
			self.db.execute("DELETE FROM mirror_files WHERE mirror=%s AND filename=%s",
				self.id, file)

		logging.info("Successfully updated mirror filelist from %s" % self.hostname)

	@property
	def prefer_for_countries(self):
		countries = self._info.get("prefer_for_countries", "")
		if countries:
			return sorted(countries.split(", "))

		return []

	@property
	def prefer_for_countries_names(self):
		return sorted([GeoIP().get_country_name(c) for c in self.prefer_for_countries])

	def distance_to(self, location, ignore_preference=False):
		if not location:
			return 0

		if not ignore_preference and location.country_code.lower() in self.prefer_for_countries:
			return 0

		distance_vector = (
			self.latitude - location.latitude,
			self.longitude - location.longitude
		)

		distance = 0
		for i in distance_vector:
			distance += i**2

		return math.sqrt(distance)

	def traffic(self, since):
		# XXX needs to be done better

		files = {}
		for entry in self.db.query("SELECT filename, filesize FROM files"):
			files[entry.filename] = entry.filesize

		query = "SELECT COUNT(filename) as count, filename FROM log_download WHERE mirror = %s"
		query += " AND date >= %s GROUP BY filename"

		traffic = 0
		for entry in self.db.query(query, self.id, since):
			if files.has_key(entry.filename):
				traffic += entry.count * files[entry.filename]

		return traffic

	@property
	def priority(self):
		return self._info.get("priority", 10)

