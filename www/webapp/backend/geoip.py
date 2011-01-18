#!/usr/bin/python

import re

from databases import Databases
from memcached import Memcached
from misc import Singleton

class GeoIP(object):
	__metaclass__ = Singleton

	def __init__(self):
		self.__country_codes = self.db.query("SELECT code, name FROM iso3166_countries")

	@property
	def db(self):
		return Databases().geoip

	@property
	def memcached(self):
		return Memcached()

	def __encode_ip(self, addr):
		# We get a tuple if there were proxy headers.
		addr = addr.split(", ")
		if addr:
			addr = addr[-1]

		# ip is calculated as described in http://ipinfodb.com/ip_database.php
		a1, a2, a3, a4 = addr.split(".")

		return int(((int(a1) * 256 + int(a2)) * 256 + int(a3)) * 256 + int(a4) + 100)

	def get_country(self, addr):
		addr = self.__encode_ip(addr)

		mem_id = "geoip-country-%s" % addr
		ret = self.memcached.get(mem_id)

		if not ret:
			ret = self.db.get("SELECT * FROM ip_group_country WHERE ip_start <= %s \
				ORDER BY ip_start DESC LIMIT 1;", addr).country_code.lower()
			self.memcached.set(mem_id, ret, 3600)

		return ret

	def get_all(self, addr):
		addr = self.__encode_ip(addr)

		mem_id = "geoip-all-%s" % addr
		ret = self.memcached.get(mem_id)

		if not ret:
			# XXX should be done with a join
			location = self.db.get("SELECT location FROM ip_group_city WHERE ip_start <= %s \
				ORDER BY ip_start DESC LIMIT 1;", addr).location

			ret = self.db.get("SELECT * FROM locations WHERE id = %s", int(location))
			self.memcached.set(mem_id, ret, 3600)

		# If location was not determinable
		if ret.latitude == 0 and ret.longitude == 0:
			return None

		return ret

	def get_country_name(self, code):
		name = "Unknown"

		code = code.upper()
		for country in self.__country_codes:
			if country.code == code:
				name = country.name
				break

		# Fix some weird strings
		name = re.sub(r"(.*) (.* Republic of)", r"\2 \1", name)

		return name


if __name__ == "__main__":
	g = GeoIP()

	print g.get_country("123.123.123.123")
	print g.get_all("123.123.123.123")
