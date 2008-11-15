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
from git import *

def give_403():
	print "Status: 403 Forbidden"
	print "Pragma: no-cache"
	print "Cache-control: no-cache"
	print "Connection: close"
	print
	print
	os._exit(0)

def give_404():
	print "Status: 404 Not found"
	print "Pragma: no-cache"
	print "Cache-control: no-cache"
	print "Connection: close"
	print
	print
	os._exit(0)

def give_302():
	print "Status: 302 Moved"
	print "Location: /"
	print "Pragma: no-cache"
	print "Cache-control: no-cache"
	print "Connection: close"
	print
	print
	os._exit(0)

class NotFoundError(Exception):
	pass

class SourceObject:
	def __init__(self, path):
		self.path = path

		self.object_type = None

		# Init hashes
		self.hash_md5 = None
		self.hash_sha1 = None

	def hash(self):
		## This is for python 2.4.
		#import md5
		#self.hash_md5 = md5.new(self.data()).hexdigest()

		import sha
		self.hash_sha1 = sha.new(self.data()).hexdigest()

	def data(self):
		return self.filedata

	def run(self):
		self.hash()
		self.showhttpheaders()
		print self.data()

	def showhttpheaders(self):
		print "Pragma: no-cache"
		print "Cache-control: no-cache"
		print "Connection: close"
		print "Content-type:" + self.mimetype()
		print "Content-length: %s" % len(self.data())
		if self.object_type:
			print "X-Object:" + self.object_type
		if self.hash_md5:
			print "X-MD5:" + self.hash_md5
		if self.hash_sha1:
			print "X-SHA1:" + self.hash_sha1
		print
		# An empty line ends the header

class FileObject(SourceObject):
	def __init__(self, path, version, url="/srv/www/ipfire.org/source/"):
		SourceObject.__init__(self, path)
		self.url= os.path.join(url, "source-%s" % version)
		self.filepath = os.path.join(self.url, path)
		self.init_file()
		
		self.object_type = "FileObject"

	def init_file(self):
		try:
			f = open(self.filepath, "rb")
		except:
			raise NotFoundError

		self.filedata = f.read()
		f.close()

	def mimetype(self):
		default_mimetype = "text/plain"
		from mimetypes import guess_type
		return guess_type(self.filepath)[0] or default_mimetype

class PatchObject(SourceObject):
	def __init__(self, path, url="/srv/git/patches.git"):
		SourceObject.__init__(self, path)

		self.object_type = "PatchObject"

		self.url = url
		self.init_repo()

	def init_repo(self):
		# init the repo
		self.repo = Repository(self.url)

		# head, tree & blob
		#self.head = self.repo.head()
		self.tree = self.repo.head.tree

		self.blob = self.set_blob()

	def set_blob(self):
		blob = None
 
		for directory in self.tree.keys():
			if isinstance(self.tree[directory], Blob):
				continue
			try:
				blob = self.tree[directory][path]
				if blob:
					break
			except KeyError:
				pass
		
		if not blob:
			raise NotFoundError

		blob._load()
		self.filedata = blob._contents
		self.filedata += '\n'
		return blob

	def mimetype(self):
		return "text/plain" #self.blob.mime_type

# main()
path = cgi.FieldStorage().getfirst('path')
ver = cgi.FieldStorage().getfirst('ver')

if not os.environ["HTTP_USER_AGENT"].startswith("IPFireSourceGrabber"):
	give_403()

if not path:
	give_302()

if not ver:
	ver = "3.x"

# At first, we assume that the requested object is a plain file:
try:
	object = FileObject(path=path, version=ver)
except NotFoundError:
	# Second, we assume that the requestet object is in the patch repo:
	try:
		object = PatchObject(path=path)
	except NotFoundError:
		give_404()
	else:
		object.run()
else:
	object.run()
