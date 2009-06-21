#!/usr/bin/python
###############################################################################
#                                                                             #
# IPFire.org - A linux based firewall                                         #
# Copyright (C) 2007  Michael Tremer & Christian Schmidt                      #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                             #
###############################################################################

import os
import cgi
import sys
import sha
from pysqlite2 import dbapi2 as sqlite

sys.path.append(".")

from git import *

SOURCE_BASE = "/srv/sources"

def give_403():
	print "Status: 403 Forbidden"
	print "Pragma: no-cache"
	print "Cache-control: no-cache"
	print "Connection: close"
	print
	print
	sys.exit()

def give_404():
	print "Status: 404 Not found"
	print "Pragma: no-cache"
	print "Cache-control: no-cache"
	print "Connection: close"
	print
	print
	sys.exit()

def give_302():
	print "Status: 302 Moved"
	print "Location: /"
	print "Pragma: no-cache"
	print "Cache-control: no-cache"
	print "Connection: close"
	print
	print
	sys.exit()

class NotFoundError(Exception):
	pass

class SourceObject:
	def __init__(self, file):
		self.file = file

		self.db = sqlite.connect("hashes.db")
		c = self.db.cursor()
		c.execute("CREATE TABLE IF NOT EXISTS hashes(file, sha1)")
		c.close()

	def getHash(self, type="sha1"):
		hash = None
		c = self.db.cursor()
		c.execute("SELECT %s FROM hashes WHERE file = '%s'" % (type, self.file,))
		try:
			hash = c.fetchone()[0]
		except TypeError:
			pass
		c.close()

		if not hash:
			hash = sha.new(self.filedata).hexdigest()
			c = self.db.cursor()
			c.execute("INSERT INTO hashes(file, sha1) VALUES('%s', '%s')" % \
				(self.file, hash,))
			c.close()
			self.db.commit()
		return hash

	def __call__(self):
		print "Status: 200 - OK"
		print "Pragma: no-cache"
		print "Cache-control: no-cache"
		print "Connection: close"
		print "Content-type: " + self.getMimetype()
		print "Content-length: %s" % len(self.filedata)
		print "X-SHA1: " + self.getHash("sha1")
		print "X-Object: %s" % str(self.__class__).split(".")[1]
		print # An empty line ends the header
		print self.filedata


class FileObject(SourceObject):
	def __init__(self, path, file):
		SourceObject.__init__(self, file)
		self.path = path
		self.filepath = "/%s/%s/%s" % (SOURCE_BASE, path, file,)

		try:
			f = open(self.filepath, "rb")
		except:
			raise NotFoundError

		self.filedata = f.read()
		f.close()

	def getMimetype(self):
		default_mimetype = "text/plain"
		from mimetypes import guess_type
		return guess_type(self.filepath)[0] or default_mimetype


class PatchObject(SourceObject):
	def __init__(self, file, url="/srv/git/patches.git"):
		SourceObject.__init__(self, file)
		self.url = url

		self.repo = Repository(self.url)
		tree = self.repo.head.tree
		blob = None

		for directory in tree.keys():
			if isinstance(tree[directory], Blob):
				continue
			try:
				blob = tree[directory][self.file]
				if blob:
					break
			except KeyError:
				pass

		if not blob:
			raise NotFoundError

		blob._load()
		self.filedata = blob._contents
		self.filedata += '\n'

	def getMimetype(self):
		return "text/plain"


def main():
	os.environ["QUERY_STRING"] = \
		os.environ["QUERY_STRING"].replace("+", "%2b")

	file = cgi.FieldStorage().getfirst("file")
	path = cgi.FieldStorage().getfirst("path")

	if not file:
		give_302()

	if not path or path == "download":
		path = "source-3.x"

	# At first, we assume that the requested object is a plain file:
	try:
		object = FileObject(path=path, file=file)
	except NotFoundError:
		# Second, we assume that the requestet object is in the patch repo:
		try:
			object = PatchObject(file=file)
		except NotFoundError:
			give_404()
		else:
			object()
	else:
		object()

try:
	main()
except SystemExit:
	pass
