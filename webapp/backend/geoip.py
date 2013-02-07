#!/usr/bin/python

import re

from databases import Databases
from memcached import Memcached
from misc import Singleton

class GeoIP(object):
	__metaclass__ = Singleton

	@property
	def db(self):
		return Databases().geoip

	def _encode_ip(self, addr):
		# We get a tuple if there were proxy headers.
		addr = addr.split(", ")
		if addr:
			addr = addr[-1]

		# ip is calculated as described in http://dev.maxmind.com/geoip/csv
		a1, a2, a3, a4 = addr.split(".")

		try:
			a1 = int(a1)
			a2 = int(a2)
			a3 = int(a3)
			a4 = int(a4)
		except ValueError:
			return 0

		return (16777216 * a1) + (65536 * a2) + (256 * a3) + a4

	def get_country(self, addr):
		addr = self._encode_ip(addr)

		ret = self.db.get("SELECT locations.country_code AS country_code FROM addresses \
			JOIN locations ON locations.id = addresses.location \
			WHERE %s BETWEEN start_ip_num AND end_ip_num LIMIT 1", addr)

		if ret:
			return ret.country_code

	def get_all(self, addr):
		addr = self._encode_ip(addr)
		if not addr:
			return

		ret = self.db.get("SELECT locations.* FROM addresses \
			JOIN locations ON locations.id = addresses.location \
			WHERE %s BETWEEN start_ip_num AND end_ip_num LIMIT 1", addr)

		if not ret:
			return

		# If location was not determinable
		if ret.latitude == 0 and ret.longitude == 0:
			return None

		return ret

	def get_country_name(self, code):
		name = "Unkown"

		codes = {
			"A1" : "Anonymous Proxy",
			"A2" : "Satellite Provider",
			"EU" : "Europe",
			"AP" : "Asia/Pacific Region",
		}

		# Return description of some exceptional codes.
		try:
			return codes[code]
		except KeyError:
			pass

		ret = self.db.get("SELECT name FROM iso3166_countries WHERE code = %s LIMIT 1", code)
		if ret:
			name = ret.name

		# Fix some weird strings
		name = re.sub(r"(.*) (.* Republic of)", r"\2 \1", name)

		return name


if __name__ == "__main__":
	g = GeoIP()

	print g.get_country("123.123.123.123")
	print g.get_all("123.123.123.123")
