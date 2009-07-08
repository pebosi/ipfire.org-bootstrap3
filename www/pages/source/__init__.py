#!/usr/bin/python

SOURCE_BASE="/srv/sources"
SOURCE_HASHES="/srv/www/ipfire.org/source/hashes.db"

SOURCE_URL="http://source.ipfire.org"

import os
import sha
from pysqlite2 import dbapi2 as sqlite

import web
import web.elements

class SourceObject:
	def __init__(self, db, file):
		self.file = file
		self.name = os.path.basename(file)

		if db:
			self.db = db
		else:
			self.db = sqlite.connect(SOURCE_HASHES)
			c = self.db.cursor()
			c.execute("CREATE TABLE IF NOT EXISTS hashes(file, sha1)")
			c.close()
		
	def data(self):
		f = open(self.file, "rb")
		data = f.read()
		f.close()
		return data

	def getHash(self, type="sha1"):
		hash = None
		c = self.db.cursor()
		c.execute("SELECT %s FROM hashes WHERE file = '%s'" % (type, self.name,))
		try:
			hash = c.fetchone()[0]
		except TypeError:
			pass
		c.close()

		if not hash:
			hash = sha.new(self.data()).hexdigest()
			c = self.db.cursor()
			c.execute("INSERT INTO hashes(file, sha1) VALUES('%s', '%s')" % \
				(self.name, hash,))
			c.close()
			self.db.commit()
		return hash


class Content(web.Content):
	def __init__(self):
		web.Content.__init__(self)
		
		self.dirs = []

		# Open database
		db = sqlite.connect(SOURCE_HASHES)
		
		for dir, subdirs, files in os.walk(SOURCE_BASE):
			if not files:
				continue
			fileobjects = []
			files.sort()
			for file in files:
				file = os.path.join(dir, file)
				fileobjects.append(SourceObject(db, file))
			self.dirs.append((os.path.basename(dir), fileobjects))
		
	def __call__(self, lang):
		ret = ""
		self.w("<h3>IPFire Source Base</h3>")
		for dir, files in self.dirs:
			b = web.elements.Box(dir)
			b.w("<ul>")
			for file in files:
				b.w("""<li style="font-family: courier;">%(hash)s | <a href="%(url)s/%(dir)s/%(file)s">%(file)s</a></li>""" % \
					{ "file" : file.name,
					  "hash" : file.getHash() or "0000000000000000000000000000000000000000",
					  "dir"  : dir,
					  "url"  : SOURCE_URL, })
			b.w("</ul>")
			ret += b()
		return ret

page = web.Page()
page.content = Content()
page.sidebar = web.elements.Sidebar()
