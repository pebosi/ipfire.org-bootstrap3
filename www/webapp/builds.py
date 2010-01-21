#!/usr/bin/python

import os
import time

from helpers import size
from info import info

def find():
	ret = []
	for item in info["nightly_builds"]:
		path = item.get("path", None)
		if not path or not os.path.exists(path):
			continue

		for host in os.listdir(path):
			for build in os.listdir(os.path.join(path, host)):
				ret.append(Build(os.path.join(path, host, build)))

	return ret

class Build(object):
	def __init__(self, path):
		self.path = path

		self.__buildinfo = None
	
	@property
	def buildinfo(self):
		if not self.__buildinfo:
			f = open(os.path.join(self.path, ".buildinfo"))
			self.__buildinfo = f.readlines()
			f.close()
		return self.__buildinfo

	def get(self, key):
		key = key.upper() + "="
		for line in self.buildinfo:
			if line.startswith(key):
				return line[len(key):].strip("\n")

	@property
	def build_host(self):
		return self.get("hostname")

	@property
	def release(self):
		return self.get("release")

	@property
	def time(self):
		return time.localtime(float(self.get("date")))

	@property
	def date(self):
		return time.strftime("%a, %Y-%m-%d %H:%M", self.time)

	@property
	def arch(self):
		return self.get("arch")

	@property
	def iso(self):
		return self.get("iso")

	@property
	def size(self):
		return size(os.path.getsize(os.path.join(self.path, self.iso)))

	@property
	def packages(self):
		path = "%s/packages_%s" % (self.path, self.arch,)
		if not os.path.exists(path):
			return []
		return os.listdir(path)

	@property
	def pxe(self):
		dir = "/srv/www/ipfire.org/pxe"
		if not os.path.isdir(dir):
			return ""

		for iso in os.listdir(dir):
			# Skip non-iso files
			if not iso.endswith(".iso"):
				continue
			if os.readlink(os.path.join(dir, iso)) == os.path.join(self.path, self.iso):
				return "[PXE]"
		return ""
