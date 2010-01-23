#!/usr/bin/python

import tornado.httpclient

import random
import threading
import time

from helpers import Item, _stringify, ping, json_loads

class Mirrors(threading.Thread):
	def __init__(self, filename):
		threading.Thread.__init__(self, name="Mirror Monitor")

		self.items = []
		self.load(filename)

		self.__running = True

		self.start()

	def load(self, filename):
		f = open(filename)
		data = f.read()
		f.close()
		
		for item in json_loads(data):
			self.items.append(MirrorItem(**_stringify(item)))

	@property
	def all(self):
		return sorted(self.items)

	@property
	def random(self):
		# Doesnt work :(
		#return random.shuffle(self.items)
		ret = []
		items = self.items[:]
		while items:
			rnd = random.randint(0, len(items)-1)
			ret.append(items.pop(rnd))
		return ret

	@property
	def reachable(self):
		ret = []
		for mirror in self.items:
			if not mirror.reachable:
				continue
			ret.append(mirror)
		return ret

	@property
	def unreachable(self):
		ret = []
		for mirror in self.all:
			if mirror in self.reachable:
				continue
			ret.append(mirror)
		return ret

	def pickone(self, reachable=False):
		mirrors = self.items
		if reachable:
			mirrors = self.reachable
		if not mirrors:
			return None
		return random.choice(mirrors)

	def with_file(self, path):
		ret = []
		for mirror in self.random:
			if not mirror["serves"]["isos"]:
				continue
			if path in mirror.files:
				ret.append(mirror)
		return ret

	def shutdown(self):
		self.__running = False

	def run(self):
		for mirror in self.random:
			if not self.__running:
				return
			mirror.update()

		count = 0
		while self.__running:
			if not count:
				count = 300 # 30 secs
				mirror = self.pickone()
				if mirror:
					mirror.update()

			time.sleep(0.1)
			count -= 1


class MirrorItem(Item):
	def __init__(self, *args, **kwargs):
		Item.__init__(self, *args, **kwargs)

		self.filelist = MirrorFilelist(self)
		self.latency = "N/A"

	def __cmp__(self, other):
		return cmp(self.name, other.name)

	def update(self):
		self.latency = ping(self.hostname) or "N/A"
		if self.filelist.outdated:
			self.filelist.update()

	@property
	def reachable(self):
		return not self.latency == "N/A"

	@property
	def url(self):
		ret = "http://" + self.hostname
		if not self.path.startswith("/"):
			ret += "/"
		ret += self.path
		if not ret.endswith("/"):
			ret += "/"
		return ret

	@property
	def files(self):
		return self.filelist.files

	def has_file(self, path):
		return path in self.files


class MirrorFilelist(object):
	def __init__(self, mirror):
		self.mirror = mirror

		self.__files = []
		self.__time = 0

		#self.update(now=True)

	def update(self, now=False):
		args = {}
		
		if now:
			while not self.mirror.reachable:
				time.sleep(10)

		http = tornado.httpclient.HTTPClient()

		if not now:
			http = tornado.httpclient.AsyncHTTPClient()
			args["callback"] = self.on_response

		try:
			reponse = http.fetch(self.mirror.url + ".filelist", **args)
		except tornado.httpclient.HTTPError:
			self.__time = time.time()
			return

		if now:
			self.on_response(reponse)

	def on_response(self, response):
		self.__files = []
		self.__time = time.time()

		if not response.code == 200:
			return

		# If invalid html content...
		if response.body.startswith("<!"):
			return

		for line in response.body.split("\n"):
			if not line:
				continue
			self.__files.append(line)

	@property
	def outdated(self):
		return (time.time() - self.__time) > 60*60

	@property
	def files(self):
		#if self.outdated:
		#	self.update()
		return self.__files


mirrors = Mirrors("mirrors.json")
