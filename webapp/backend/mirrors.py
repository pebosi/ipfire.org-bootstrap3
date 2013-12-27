#!/usr/bin/python

from __future__ import division

import datetime
import logging
import math
import os.path
import random
import socket
import time
import tornado.httpclient
import tornado.netutil
import urlparse

from misc import Object

class Downloads(Object):
	@property
	def total(self):
		ret = self.db.get("SELECT COUNT(*) AS total FROM log_download")

		return ret.total

	@property
	def today(self):
		ret = self.db.get("SELECT COUNT(*) AS today FROM log_download WHERE date::date = NOW()::date")

		return ret.today

	@property
	def yesterday(self):
		ret = self.db.get("SELECT COUNT(*) AS yesterday FROM log_download WHERE date::date = (NOW() - INTERVAL '1 day')::date")

		return ret.yesterday

	@property
	def daily_map(self):
		ret = self.db.query("SELECT date::date AS date, COUNT(*) AS downloads FROM log_download"
			" WHERE date::date BETWEEN (NOW() - INTERVAL '30 days')::date AND NOW()::date GROUP BY date::date")

		return ret

	def get_countries(self, duration="all"):
		query = "SELECT country_code, count(country_code) AS count FROM log_download"

		if duration == "today":
			query += " WHERE date::date = NOW()::date"

		query += " GROUP BY country_code ORDER BY count DESC"

		results = self.db.query(query)
		ret = {}

		count = sum([o.count for o in results])
		if count:
			for res in results:
				ret[res.country_code] = res.count / count

		return ret

	def get_mirror_load(self, duration="all"):
		query = "SELECT mirror, COUNT(mirror) AS count FROM log_download"

		if duration == "today":
			query += " WHERE date::date = NOW()::date"

		query += " GROUP BY mirror ORDER BY count DESC"

		results = self.db.query(query)
		ret = {}

		count = sum([o.count for o in results])
		if count:
			for res in results:
				mirror = self.mirrors.get(res.mirror)
				ret[mirror.hostname] = res.count / count

		return ret


class Mirrors(Object):
	def check_all(self):
		for mirror in self.get_all():
			mirror.check()

	def get(self, id):
		return Mirror(self.backend, id)

	def get_all(self):
		res = self.db.query("SELECT * FROM mirrors WHERE enabled = %s", True)

		mirrors = []
		for row in res:
			mirror = Mirror(self.backend, row.id, row)
			mirrors.append(mirror)

		return MirrorSet(self.backend, sorted(mirrors))

	def get_all_up(self):
		res = self.db.query("SELECT * FROM mirrors WHERE enabled = %s AND state = %s \
			ORDER BY hostname", True, "UP")

		mirrors = []
		for row in res:
			m = Mirror(self.backend, row.id, row)
			mirrors.append(m)

		return MirrorSet(self.backend, mirrors)

	def get_by_hostname(self, hostname):
		mirror = self.db.get("SELECT id FROM mirrors WHERE hostname=%s", hostname)

		return Mirror(self.backend, mirror.id)

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

		return mirrors

	def get_for_country(self, country):
		# XXX need option for random order
		mirrors = self.db.query("SELECT id FROM mirrors WHERE prefer_for_countries LIKE %s", country)

		for mirror in mirrors:
			yield self.get(mirror.id)

	def get_for_location(self, location):
		if not location:
			return None

		distance = 2500

		mirrors = []
		all_mirrors = self.get_all()

		while all_mirrors and len(mirrors) <= 3 and distance <= 8000:
			for mirror in all_mirrors:
				mirror_distance = mirror.distance_to(location)
				if mirror_distance is None:
					continue

				if mirror_distance<= distance:
					mirrors.append(mirror)
					all_mirrors.remove(mirror)

			distance *= 1.2

		return mirrors

	def get_all_files(self):
		files = []

		for mirror in self.get_all():
			if not mirror.state == "UP":
				continue

			for file in mirror.filelist:
				if not file in files:
					files.append(file)

		return files


class MirrorSet(Object):
	def __init__(self, backend, mirrors):
		Object.__init__(self, backend)

		self._mirrors = mirrors

	def __add__(self, other):
		mirrors = []

		for mirror in self._mirrors + other._mirrors:
			if mirror in mirrors:
				continue

			mirrors.append(mirror)

		return MirrorSet(self.backend, mirrors)

	def __sub__(self, other):
		mirrors = self._mirrors[:]

		for mirror in other._mirrors:
			if mirror in mirrors:
				mirrors.remove(mirror)

		return MirrorSet(self.backend, mirrors)

	def __iter__(self):
		return iter(self._mirrors)

	def __len__(self):
		return len(self._mirrors)

	def __str__(self):
		return "<MirrorSet %s>" % ", ".join([m.hostname for m in self._mirrors])

	def get_with_file(self, filename):
		with_file = [m.mirror for m in self.db.query("SELECT mirror FROM mirror_files WHERE filename=%s", filename)]

		mirrors = []
		for mirror in self._mirrors:
			if mirror.id in with_file:
				mirrors.append(mirror)

		return MirrorSet(self.backend, mirrors)

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

		return MirrorSet(self.backend, mirrors)

	def get_for_location(self, location):
		distance = 2500
		mirrors = []

		if location:
			while len(mirrors) <= 3 and distance <= 8000:
				for mirror in self._mirrors:
					if mirror in mirrors:
						continue

					mirror_distance = mirror.distance_to(location)
					if mirror_distance is None:
						continue

					if mirror_distance <= distance:
						mirrors.append(mirror)

				distance *= 1.2

		return MirrorSet(self.backend, mirrors)

	def get_with_state(self, state):
		mirrors = []

		for mirror in self._mirrors:
			if mirror.state == state:
				mirrors.append(mirror)

		return MirrorSet(self.backend, mirrors)


class Mirror(Object):
	def __init__(self, backend, id, data=None):
		Object.__init__(self, backend)

		self.id = id

		if data:
			self._info = data
		else:
			self._info = self.db.get("SELECT * FROM mirrors WHERE id = %s", self.id)
		self._info["url"] = self.generate_url()

		self.__location = None
		self.__country_name = None

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.url)

	def __cmp__(self, other):
		ret = cmp(self.country_code, other.country_code)

		if not ret:
			ret = cmp(self.hostname, other.hostname)

		return ret

	def generate_url(self):
		url = "http://%s" % self.hostname
		if not self.path.startswith("/"):
			url += "/"
		url += "%s" % self.path
		if not self.path.endswith("/"):
			url += "/"
		return url

	@property
	def hostname(self):
		return self._info.hostname

	@property
	def path(self):
		return self._info.path

	@property
	def address(self):
		return socket.gethostbyname(self.hostname)

	@property
	def owner(self):
		return self._info.owner

	@property
	def location(self):
		if self.__location is None:
			self.__location = self.geoip.get_location(self.address)

		return self.__location

	@property
	def latitude(self):
		if self.location:
			return self.location.latitude

	@property
	def longitude(self):
		if self.location:
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
		if self.location:
			return self.location.country

	@property
	def country_name(self):
		if self.__country_name is None:
			self.__country_name = self.geoip.get_country_name(self.country_code)

		return self.__country_name

	@property
	def location_str(self):
		location = []

		if self._info.location:
			location.append(self._info.location)

		elif self.location:
			location.append(self.location.city)
			location.append(self.country_name)

		return ", ".join([s for s in location if s])

	@property
	def asn(self):
		if not hasattr(self, "__asn"):
			self.__asn = self.geoip.get_asn(self.address)

		return self.__asn

	@property
	def filelist(self):
		filelist = self.db.query("SELECT filename FROM mirror_files WHERE mirror=%s ORDER BY filename", self.id)
		return [f.filename for f in filelist]

	@property
	def prefix(self):
		return ""

	@property
	def url(self):
		return self._info.url

	def build_url(self, filename):
		return urlparse.urljoin(self.url, filename)

	@property
	def last_update(self):
		return self._info.last_update

	@property
	def state(self):
		return self._info.state

	def set_state(self, state):
		logging.info("Setting state of %s to %s" % (self.hostname, state))

		if self.state == state:
			return

		self.db.execute("UPDATE mirrors SET state = %s WHERE id = %s", state, self.id)

		# Reload changed settings
		if hasattr(self, "_info"):
			self._info["state"] = state

	@property
	def enabled(self):
		return self._info.enabled

	@property
	def disabled(self):
		return not self.enabled

	def check(self):
		logging.info("Running check for mirror %s" % self.hostname)

		self.check_timestamp()
		self.check_filelist()

	def check_state(self):
		logging.debug("Checking state of mirror %s" % self.id)

		if not self.enabled:
			self.set_state("DOWN")
			return

		now = datetime.datetime.utcnow()

		time_delta = now - self.last_update
		time_diff = time_delta.total_seconds()

		time_down = self.settings.get_int("mirrors_time_down", 3*24*60*60)
		if time_diff >= time_down:
			self.set_state("DOWN")
			return

		time_outofsync = self.settings.get_int("mirrors_time_outofsync", 6*60*60)
		if time_diff >= time_outofsync:
			self.set_state("OUTOFSYNC")
			return

		self.set_state("UP")

	def check_timestamp(self):
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

		timestamp = datetime.datetime.fromtimestamp(timestamp)

		self.db.execute("UPDATE mirrors SET last_update = %s WHERE id = %s",
			timestamp, self.id)

		# Reload changed settings
		if hasattr(self, "_info"):
			self._info["timestamp"] = timestamp

		self.check_state()

		logging.info("Successfully updated timestamp from %s" % self.hostname)

	def check_filelist(self):
		# XXX need to remove data from disabled mirrors
		if not self.enabled:
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
		countries = [self.geoip.get_country_name(c.upper()) for c in self.prefer_for_countries]

		return sorted(countries)

	def distance_to(self, location, ignore_preference=False):
		if not location:
			return None

		country_code = None
		if location.country:
			country_code = location.country.lower()

		if not ignore_preference and country_code in self.prefer_for_countries:
			return 0

		# http://www.movable-type.co.uk/scripts/latlong.html

		if self.latitude is None:
			return None

		if self.longitude is None:
			return None

		earth = 6371 # km
		delta_lat = math.radians(self.latitude - location.latitude)
		delta_lon = math.radians(self.longitude - location.longitude)

		lat1 = math.radians(self.latitude)
		lat2 = math.radians(location.latitude)

		a = math.sin(delta_lat / 2) ** 2
		a += math.cos(lat1) * math.cos(lat2) * (math.sin(delta_lon / 2) ** 2)

		b1 = math.sqrt(a)
		b2 = math.sqrt(1 - a)

		c = 2 * math.atan2(b1, b2)

		return c * earth

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

	@property
	def development(self):
		return self._info.get("development", False)

	@property
	def mirrorlist(self):
		return self._info.get("mirrorlist", False)

	@property
	def addresses(self):
		if not hasattr(self, "__addresses"):
			addrinfo = socket.getaddrinfo(self.hostname, 0, socket.AF_UNSPEC, socket.SOCK_STREAM)

			ret = []
			for family, socktype, proto, canonname, address in addrinfo:
				if family == socket.AF_INET:
					address, port = address
				elif family == socket.AF_INET6:
					address, port, flowid, scopeid = address
				ret.append((family, address))

			self.__addresses = ret

		return self.__addresses

	@property
	def addresses6(self):
		return [address for family, address in self.addresses if family == socket.AF_INET6]

	@property
	def addresses4(self):
		return [address for family, address in self.addresses if family == socket.AF_INET]
