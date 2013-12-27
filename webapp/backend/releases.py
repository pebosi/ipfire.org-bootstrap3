#!/usr/bin/python

import hashlib
import logging
import os
import re
import urllib
import urlparse

import database
import tracker
from misc import Object

class File(Object):
	def __init__(self, backend, release, id, data=None):
		Object.__init__(self, backend)

		self.id = id
		self._release = release

		# get all data from database
		self.__data = data

	def __cmp__(self, other):
		return cmp(self.prio, other.prio)

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

		elif "armv5tel" in filename and "scon" in filename:
			return "armv5tel-scon"

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
		baseurl = self.settings.get("download_url", "http://downloads.ipfire.org")

		return urlparse.urljoin(baseurl, self.filename)

	@property
	def desc(self):
		_ = lambda x: x

		descriptions = {
			"armv5tel"	: _("Image for the armv5tel architecture"),
			"armv5tel-scon"	: _("armv5tel image for boards with serial console"),
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
			"armv5tel"	: 40,
			"armv5tel-scon"	: 41,
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
			"armv5tel-scon"	: _("This image runs on ARM boards with a serial console"),
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


class Release(Object):
	def __init__(self, backend, id, data=None):
		Object.__init__(self, backend)
		self.id = id

		# get all data from database
		self.__data = data or self.db.get("SELECT * FROM releases WHERE id = %s", self.id)
		assert self.__data

		self.__files = []

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.name)

	def __cmp__(self, other):
		return cmp(self.id, other.id)

	@property
	def files(self):
		if not self.__files:
			files = self.db.query("SELECT * FROM files WHERE releases = %s \
				AND NOT filename LIKE '%%.torrent'", self.id)

			self.__files = [File(self.backend, self, f.id, f) for f in files]
			self.__files.sort()

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
		return self.__data.name

	@property
	def sname(self):
		return self.__data.sname

	@property
	def stable(self):
		return self.__data.stable

	@property
	def published(self):
		return self.__data.published

	date = published

	@property
	def path(self):
		return self.__data.path

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

			logging.info("Hashing %s..." % filename)
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

	def is_netboot_capable(self):
		return self.path and "ipfire-2.x" in self.path

	@property
	def netboot_kernel(self):
		return "http://downloads.ipfire.org/%s/images/vmlinuz" % self.path

	@property
	def netboot_initrd(self):
		return "http://downloads.ipfire.org/%s/images/instroot" % self.path

	@property
	def netboot_append(self):
		return "ro"


class Releases(Object):
	def get_by_id(self, id):
		ret = self.db.get("SELECT * FROM releases WHERE id = %s", id)

		if ret:
			return Release(self.backend, ret.id, data=ret)

	def get_by_sname(self, sname):
		ret = self.db.get("SELECT * FROM releases WHERE sname = %s", sname)

		if ret:
			return Release(self.backend, ret.id, data=ret)

	def get_latest(self, stable=True):
		ret = self.db.get("SELECT * FROM releases WHERE published IS NOT NULL AND published <= NOW() \
			AND stable = %s ORDER BY published DESC LIMIT 1", stable)

		if ret:
			return Release(self.backend, ret.id, data=ret)

	def get_stable(self):
		query = self.db.query("SELECT * FROM releases \
			WHERE published IS NOT NULL AND published <= NOW() AND stable = TRUE \
			ORDER BY published DESC")

		releases = []
		for row in query:
			release = Release(self.backend, row.id, data=row)
			releases.append(release)

		return releases

	def get_unstable(self):
		query = self.db.query("SELECT * FROM releases \
			WHERE published IS NOT NULL AND published <= NOW() AND stable = FALSE \
			ORDER BY published DESC")

		releases = []
		for row in query:
			release = Release(self.backend, row.id, data=row)
			releases.append(release)

		return releases

	def get_all(self):
		query = self.db.query("SELECT * FROM releases \
			WHERE published IS NOT NULL AND published <= NOW() \
			ORDER BY published DESC")

		releases = []
		for row in query:
			release = Release(self.backend, row.id, data=row)
			releases.append(release)

		return releases

	def get_file_for_torrent_hash(self, torrent_hash):
		file = self.db.get("SELECT id, releases FROM files WHERE torrent_hash = %s LIMIT 1",
			torrent_hash)

		if not file:
			return

		release = Release(file.releases)
		file = File(release, file.id)

		return file
