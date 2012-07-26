#!/usr/bin/python

import hashlib
import logging
import os
import re
import urllib
import urlparse

import tracker

from databases import Databases
from misc import Singleton
from settings import Settings

class File(object):
	def __init__(self, release, id):
		self.id = id
		self._release = release

		# get all data from database
		self.__data = None

	@property
	def db(self):
		return Databases().webapp

	@property
	def tracker(self):
		return self.release.tracker

	@property
	def data(self):
		if self.__data is None:
			self.__data = self.db.get("SELECT * FROM files WHERE id = %s", self.id)
			assert self.__data

		return self.__data

	@property
	def release(self):
		if not self._release:
			release_id = self.data.get("releases")
			self._release = Release(release_id)

		return self._release

	@property
	def type(self):
		filename = self.filename

		if filename.endswith(".iso"):
			return "iso"

		elif filename.endswith(".torrent"):
			return "torrent"

		elif "xen" in filename:
			return "xen"

		elif "sources" in filename:
			return "source"

		elif "usb-fdd" in filename:
			return "usbfdd"

		elif "usb-hdd" in filename:
			return "usbhdd"

		elif "armv5tel" in filename:
			return "armv5tel"

		elif "scon" in filename:
			return "alix"

		elif filename.endswith(".img.gz"):
			return "flash"

		else:
			return "unknown"

	@property
	def url(self):
		baseurl = Settings().get("download_url")

		return urlparse.urljoin(baseurl, self.filename)

	@property
	def desc(self):
		_ = lambda x: x

		descriptions = {
			"armv5tel"	: _("Image for the armv5tel architecture"),
			"iso"		: _("Installable CD image"),
			"torrent"	: _("Torrent file"),
			"flash"		: _("Flash image"),
			"alix"		: _("Alix image"),
			"usbfdd"	: _("USB FDD Image"),
			"usbhdd"	: _("USB HDD Image"),
			"xen"		: _("Pregenerated Xen image"),
		}

		try:
			return descriptions[self.type]
		except KeyError:
			return _("Unknown image type")

	@property
	def prio(self):
		priorities = {
			"iso"		: 10,
			"torrent"	: 20,
			"flash"		: 40,
			"alix"		: 41,
			"usbfdd"	: 31,
			"usbhdd"	: 30,
			"armv5tel"  : 40,
			"xen"		: 50,
		}
		
		try:
			return priorities[self.type]
		except KeyError:
			return 999

	@property
	def rem(self):
		_ = lambda x: x
	
		remarks = {
			"armv5tel"	: _("This image runs on many ARM-based boards"),
			"iso"		: _("Use this image to burn a CD and install IPFire from it."),
			"torrent"	: _("Download the CD image from the torrent network."),
			"flash"		: _("An image that is meant to run on embedded devices."),
			"alix"		: _("Flash image where a serial console is enabled by default."),
			"usbfdd"	: _("Install IPFire from a floppy-formated USB key."),
			"usbhdd"	: _("If the floppy image doesn't work, use this image instead."),
			"xen"		: _("A ready-to-run image for Xen."),
		}

		try:
			return remarks[self.type]
		except KeyError:
			return _("Unknown image type")

	@property
	def sha1(self):
		return self.data.get("sha1")

	@property
	def filename(self):
		return self.data.get("filename")

	@property
	def basename(self):
		return os.path.basename(self.filename)

	@property
	def size(self):
		return self.data.get("filesize")

	@property
	def arch(self):
		known_arches = ("i586", "arm")

		for arch in known_arches:
			if arch in self.basename:
				return arch

		return "N/A"

	@property
	def torrent_hash(self):
		return self.data.get("torrent_hash", None)

	@property
	def magnet_link(self):
		# Don't return anything if we have no torrent hash.
		if self.torrent_hash is None:
			return

		s = "magnet:?xt=urn:btih:%s" % self.torrent_hash

		#s += "&xl=%d" % self.size
		s += "&dn=%s" % urllib.quote(self.basename)

		# Add our tracker.
		s += "&tr=http://tracker.ipfire.org:6969/announce"

		return s

	@property
	def seeders(self):
		if not self.torrent_hash:
			return

		return self.tracker.get_seeds(self.torrent_hash)

	@property
	def peers(self):
		if not self.torrent_hash:
			return

		return self.tracker.get_peers(self.torrent_hash)

	@property
	def completed(self):
		if not self.torrent_hash:
			return

		return self.tracker.complete(self.torrent_hash)


class Release(object):
	@property
	def db(self):
		return Releases().db

	@property
	def tracker(self):
		return tracker.Tracker()

	def __init__(self, id):
		self.id = id

		# get all data from database
		self.__data = \
			self.db.get("SELECT * FROM releases WHERE id = %s", self.id)
		assert self.__data

		self.__files = []

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.name)

	@property
	def files(self):
		if not self.__files:
			files = self.db.query("SELECT id, filename FROM files WHERE releases = %s \
					AND loadable = 'Y' AND NOT filename LIKE '%%.torrent'", self.id)

			self.__files = [File(self, f.id) for f in files]
			self.__files.sort(lambda a, b: cmp(a.prio, b.prio))

		return self.__files

	@property
	def torrents(self):
		torrents = []

		for file in self.files:
			if not file.torrent_hash:
				continue

			torrents.append(file)

		return torrents

	@property
	def name(self):
		return self.__data.get("name")

	@property
	def stable(self):
		return self.__data.get("stable")

	@property
	def published(self):
		return self.__data.get("published")

	@property
	def date(self):
		return self.__data.get("date")

	@property
	def path(self):
		return self.__data.get("path")

	def get_file(self, type):
		for file in self.files:
			if file.type == type:
				return file

	def __file_hash(self, filename):
		sha1 = hashlib.sha1()

		with open(filename) as f:
			buf_size = 1024
			buf = f.read(buf_size)
			while buf:
				sha1.update(buf)
				buf = f.read(buf_size)

		return sha1.hexdigest()

	def scan_files(self, basepath="/srv/mirror0"):
		if not self.path:
			return

		path = os.path.join(basepath, self.path)
		if not os.path.exists(path):
			return

		files = self.db.query("SELECT filename FROM files WHERE releases = %s", self.id)
		files = [f.filename for f in files]

		# Make files that do not exists not loadable.
		for filename in files:
			_filename = os.path.join(basepath, filename)
			if not os.path.exists(_filename):
				self.db.execute("UPDATE files SET loadable='N' WHERE filename = %s", filename)

		for filename in os.listdir(path):
			filename = os.path.join(path, filename)

			if os.path.isdir(filename):
				continue

			_filename = re.match(".*(releases/.*)", filename).group(1)
			if _filename in files:
				continue

			if filename.endswith(".md5"):
				continue

			filehash = self.__file_hash(filename)
			filesize = os.path.getsize(filename)

			# Check if there is a torrent download available for this file:
			torrent_hash = ""
			torrent_file = "%s.torrent" % filename
			if os.path.exists(torrent_file):
				torrent_hash = self.torrent_read_hash(torrent_file)

			self.db.execute("INSERT INTO files(releases, filename, filesize, \
				sha1, torrent_hash) VALUES(%s, %s, %s, %s, %s)",
				self.id, _filename, filesize, filehash, torrent_hash)

		# Search for all files that miss a torrent hash.
		files = self.db.query("SELECT id, filename FROM files \
			WHERE releases = %s AND torrent_hash IS NULL", self.id)

		for file in files:
			path = os.path.join(basepath, file.filename)

			torrent_file = "%s.torrent" % path
			if os.path.exists(torrent_file):
				torrent_hash = self.torrent_read_hash(torrent_file)

				self.db.execute("UPDATE files SET torrent_hash = %s WHERE id = %s",
					torrent_hash, file.id)

	def torrent_read_hash(self, filename):
		f = None
		try:
			f = open(filename, "rb")

			metainfo = tracker.bdecode(f.read())
			metainfo = tracker.bencode(metainfo["info"])

			hash = hashlib.sha1()
			hash.update(metainfo)

			return hash.hexdigest()

		finally:
			if f:
				f.close()


class Releases(object):
	__metaclass__ = Singleton

	@property
	def db(self):
		return Databases().webapp

	def list(self):
		return [Release(r.id) for r in self.db.query("SELECT id FROM releases ORDER BY date DESC")]

	def get_by_id(self, id):
		id = int(id)
		if id in [r.id for r in self.db.query("SELECT id FROM releases")]:
			return Release(id)

	def get_latest(self, stable=1):
		query = "SELECT id FROM releases WHERE published='Y' AND"
		if stable:
			query += " stable='Y'"
		else:
			query += " stable='N'"

		query += " ORDER BY date DESC LIMIT 1"

		release = self.db.get(query)
		if release:
			return Release(release.id)

	def get_stable(self):
		releases = self.db.query("""SELECT id FROM releases
			WHERE published='Y' AND stable='Y'
			ORDER BY date DESC""")

		return [Release(r.id) for r in releases]

	def get_unstable(self):
		releases = self.db.query("""SELECT id FROM releases
			WHERE published='Y' AND stable='N'
			ORDER BY date DESC""")

		return [Release(r.id) for r in releases]

	def get_all(self):
		releases = self.db.query("""SELECT id FROM releases
			WHERE published='Y' ORDER BY date DESC""")

		return [Release(r.id) for r in releases]

	def get_file_for_torrent_hash(self, torrent_hash):
		file = self.db.get("SELECT id, releases FROM files WHERE torrent_hash = %s LIMIT 1",
			torrent_hash)

		if not file:
			return

		release = Release(file.releases)
		file = File(release, file.id)

		return file


if __name__ == "__main__":
	r = Releases()

	for release in r.get_all():
		print release.name

	print r.get_latest()
