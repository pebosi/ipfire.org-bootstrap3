#!/usr/bin/python

import hashlib
import logging
import os
import re
import urlparse

from databases import Databases
from misc import Singleton
from settings import Settings

class File(object):
	def __init__(self, release, id):
		self.release = release

		# get all data from database
		self.__data = self.db.get("SELECT * FROM files WHERE id = %s", id)

	@property
	def db(self):
		return self.release.db

	@property
	def type(self):
		return self.__data.get("filetype")

	@property
	def url(self):
		baseurl = Settings().get("download_url")

		return urlparse.urljoin(baseurl, self.filename)

	@property
	def desc(self):
		_ = lambda x: x

		descriptions = {
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
		return self.__data.get("sha1")

	@property
	def filename(self):
		return self.__data.get("filename")

	@property
	def basename(self):
		return os.path.basename(self.filename)


class Release(object):
	@property
	def db(self):
		return Releases().db

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
			files = self.db.query("SELECT id FROM files WHERE releases = %s \
					AND loadable = 'Y'", self.id)

			self.__files = [File(self, f.id) for f in files]
			self.__files.sort(lambda a, b: cmp(a.prio, b.prio))

		return self.__files

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

	@property
	def torrent_hash(self):
		h = self.__data.get("torrent_hash")
		if h:
			return h.lower()

	def get_file(self, type):
		for file in self.files:
			if file.type == type:
				return file

	def __file_hash(self, filename):
		sha1 = hashlib.sha1()

		with open(filename) as f:
			sha1.update(f.read())

		return sha1.hexdigest()

	def __guess_filetype(self, filename):
		if filename.endswith(".iso"):
			return "iso"

		if filename.endswith(".torrent"):
			return "torrent"

		if "xen" in filename:
			return "xen"

		if "sources" in filename:
			return "source"

		if "usb-fdd" in filename:
			return "usbfdd"

		if "usb-hdd" in filename:
			return "usbhdd"

		if "scon" in filename:
			return "alix"

		if filename.endswith(".img.gz"):
			return "flash"

		return "unknown"

	def scan_files(self, basepath="/srv/mirror0"):
		if not self.path:
			return

		path = os.path.join(basepath, self.path)

		files = [f.filename for f in self.files]

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
			filetype = self.__guess_filetype(filename)

			self.db.execute("""INSERT INTO files(releases, filename, filesize, filetype, sha1)
				VALUES(%s, %s, %s, %s, %s)""", self.id, _filename, filesize, filetype, filehash)


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


if __name__ == "__main__":
	r = Releases()

	for release in r.get_all():
		print release.name

	print r.get_latest()
