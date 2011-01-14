#!/usr/bin/python

from databases import Databases
from misc import Singleton

class GeoIP(object):
	__metaclass__ = Singleton

	@property
	def db(self):
		return Databases().geoip

	def __encode_ip(self, addr):
		# We get a tuple if there were proxy headers.
		addr = addr.split(", ")
		if addr:
			addr = addr[-1]

		# ip is calculated as described in http://ipinfodb.com/ip_database.php
		a1, a2, a3, a4 = addr.split(".")

		return int(((int(a1) * 256 + int(a2)) * 256 + int(a3)) * 256 + int(a4) + 100)

	def get_country(self, addr):
		return self.db.get("SELECT * FROM ip_group_country WHERE ip_start <= %s \
			ORDER BY ip_start DESC LIMIT 1;", self.__encode_ip(addr)).country_code.lower()

	def get_all(self, addr):
		# XXX should be done with a join
		location = self.db.get("SELECT location FROM ip_group_city WHERE ip_start <= %s \
			ORDER BY ip_start DESC LIMIT 1;", self.__encode_ip(addr)).location
			
		return self.db.get("SELECT * FROM locations WHERE id = %s", int(location))


if __name__ == "__main__":
	g = GeoIP()

	print g.get_country("123.123.123.123")
	print g.get_all("123.123.123.123")
