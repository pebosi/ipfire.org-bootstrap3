#!/usr/bin/python

import IPy
import re

import countries

from misc import Object

class GeoIP(Object):
	def guess_address_family(self, addr):
		if ":" in addr:
			return 6

		return 4

	def get_country(self, addr):
		ret = self.get_all(addr)

		if ret:
			return ret.country

	def get_location(self, addr):
		family = self.guess_address_family(addr)

		if family == 6:
			query = "SELECT *, NULL AS city, NULL AS postal_code FROM geoip_ipv6 WHERE %s \
				BETWEEN start_ip AND end_ip LIMIT 1"
		elif family == 4:
			query = "SELECT * FROM geoip_ipv4 WHERE inet_to_bigint(%s) \
				BETWEEN start_ip AND end_ip LIMIT 1"

		return self.db.get(query, addr)

	def get_asn(self, addr):
		family = self.guess_address_family(addr)

		if family == 6:
			query = "SELECT asn FROM geoip_asnv6 WHERE %s \
				BETWEEN start_ip AND end_ip LIMIT 1"
		elif family == 4:
			query = "SELECT asn FROM geoip_asnv4 WHERE inet_to_bigint(%s) \
				BETWEEN start_ip AND end_ip LIMIT 1"

		ret = self.db.get(query, addr)

		if ret:
			return ret.asn

	def get_all(self, addr):
		location = self.get_location(addr)

		if location:
			location["asn"] = self.get_asn(addr)

		return location

	_countries = {
		"A1" : "Anonymous Proxy",
		"A2" : "Satellite Provider",
		"AP" : "Asia/Pacific Region",
		"EU" : "Europe",
	}

	def get_country_name(self, code):
		# Return description of some exceptional codes.
		try:
			return self._countries[code]
		except KeyError:
			pass

		country = countries.get_by_code(code)
		if not country:
			return code

		return country
