#!/usr/bin/python

import tornado.httpclient

import GeoIP
import random
import time

from threading import Thread

from helpers import Item, _stringify, ping, json_loads

import logging

geoip_cache = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)

continents = {
	"america"   : [ "us", ],
	"asia"      : [ "cn", "jp", ],
	"australia" : [ "au", ],
	"europe"    : [ "at", "de", "es", "fr", ],
}

def continent_by_ip(ip):
	country = geoip_cache.country_code_by_addr(ip)
	if not country:
		return

	country = country.lower()

	for continent, countries in continents.items():
		if not country in countries:
			continue
		return continent

class Mirrors(object):
	def __init__(self, application, filename):
		self.application = application
		self.items = []
		self.load(filename)

	def load(self, filename):
		f = open(filename)
		data = f.read()
		f.close()

		for item in json_loads(data):
			self.items.append(MirrorItem(**_stringify(item)))

	@property
	def master(self):
		return self.items[0]

	@property
	def all(self):
		return sorted(self.items)

	@property
	def random(self):
		mirrors = self.get()
		random.shuffle(mirrors)
		return mirrors

	@property
	def reachable(self):
		return self.filter_reachable(self.all)

	@property
	def unreachable(self):
		return self.filter_unreachable(self.all)

	def filter_continent(self, mirrors, continent):
		try:
			countries = continents[continent]
		except KeyError:
			return []

		ret = []
		for mirror in mirrors:
			if mirror.location["country_code"] in countries:
				ret.append(mirror)

		return ret

	def filter_file(self, mirrors, path):
		ret = []
		for mirror in mirrors:
			if not mirror["serves"]["isos"]:
				continue
			if path in mirror.files:
				ret.append(mirror)
		return ret

	def filter_reachable(self, mirrors):
		return [m for m in mirrors if m.reachable]

	def filter_unreachable(self, mirrors):
		return [m for m in mirrors if not m.reachable]

	def get(self, continent=None, file=None, unreachable=False, reachable=False):
		mirrors = self.all

		if continent:
			mirrors = self.filter_continent(mirrors, continent)
		if file:
			mirrors = self.filter_file(mirrors, file)
		if reachable:
			mirrors = self.filter_reachable(mirrors)
		if unreachable:
			mirrors = self.filter_unreachable(mirrors)

		return mirrors

	def pickone(self, **kwargs):
		if kwargs.has_key("ip"):
			kwargs["continent"] = continent_by_ip(kwargs.pop("ip"))

		mirrors = self.get(**kwargs)

		# If we did not get any mirrors we try a global one
		if not mirrors:
			del kwargs["continent"]
			mirrors = self.get(**kwargs)

		if not mirrors:
			return None

		return random.choice(mirrors)

	# To be removed
	def with_file(self, path):
		return self.get(file=path)

	trigger_counter = 0

	def trigger(self):
		if not self.trigger_counter:
			self.trigger_counter = 300

			for mirror in self.all:
				mirror.update()

		self.trigger_counter -= 1


class MirrorItem(object):
	def __init__(self, **kwargs):
		self.items = kwargs

		self.files = []
		self.timestamp = 0

		logging.debug("Initialized mirror %s" % self.hostname)

	def __cmp__(self, other):
		return cmp(self.owner, other.owner)

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.hostname)

	def __getattr__(self, key):
		try:
			return self.items[key]
		except KeyError:
			raise AttributeError

	def html_class(self):
		if time.time() - self.timestamp > 60*60*24:
			return "outdated"
		return "ok"

	def update(self):
		self.update_filelist()
		self.update_timestamp()

	def update_filelist(self):
		http = tornado.httpclient.AsyncHTTPClient()

		http.fetch(self.url + ".filelist",
			callback=self.__update_filelist_response)

	def __update_filelist_response(self, response):
		if response.error:
			logging.debug("Error getting filelist from %s" % self.hostname)
			return

		if not response.code == 200: 
			return

		logging.debug("Got filelist from %s" % self.hostname)

		self.files = []

		for line in response.body.splitlines():
			self.files.append(line)

	def update_timestamp(self):
		http = tornado.httpclient.AsyncHTTPClient()

		http.fetch(self.url + ".timestamp",
			callback=self.__update_timestamp_response)

	def __update_timestamp_response(self, response):
		if response.error:
			logging.debug("Error getting timestamp from %s" % self.hostname)

		data = response.body.strip()
		try:
			self.timestamp = int(data)
		except ValueError:
			self.timestamp = 0

	@property
	def url(self):
		ret = "http://" + self.hostname
		if not self.path.startswith("/"):
			ret += "/"
		ret += self.path
		if not ret.endswith("/"):
			ret += "/"
		return ret

	def filelist_compare(self, other_files):
		own_files = [f for f in self.files if f in other_files]

		try:
			return (len(own_files) * 100) / len(other_files)
		except ZeroDivisionError:
			return 0

	def has_file(self, path):
		return path in self.files
