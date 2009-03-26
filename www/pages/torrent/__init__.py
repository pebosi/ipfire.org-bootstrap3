#!/usr/bin/python

TRACKER_URL ="http://tracker.ipfire.org:6969/stats?format=txt&mode=tpbs"
TORRENT_BASE="/srv/pakfire/data/torrent"

import os
import sha
import urllib2

from client.bencode import bencode, bdecode
import web

class TrackerInfo:
	def __init__(self, url):
		self.info = {}

		f = urllib2.urlopen(url)
		for line in f.readlines():
			(hash, seeds, peers,) = line.split(":")
			self.info[hash] = (seeds, peers.rstrip("\n"),)
		f.close()

	def __call__(self):
		print self.info

	def get(self, hash):
		try:
			return self.info[hash]
		except KeyError:
			return 0, 0


class TorrentObject:
	def __init__(self, file):
		self.name = os.path.basename(file)
		f = open(file, "rb")
		self.info = bdecode(f.read())
		f.close()
	
	def __call__(self):
		print "File : %s" % self.get_file()
		print "Hash : %s" % self.get_hash()
	
	def get_hash(self):
		return sha.sha(bencode(self.info["info"])).hexdigest().upper()
	
	def get_file(self):
		return self.name


torrent_files = []
for file in os.listdir(TORRENT_BASE):
	if not file.endswith(".torrent"):
		continue
	file = os.path.join(TORRENT_BASE, file)
	torrent_files.insert(0, TorrentObject(file))


tracker = TrackerInfo(TRACKER_URL)

class TorrentBox(web.Box):
	def __init__(self, file):
		web.Box.__init__(self, file.name, file.get_hash())
		self.w("""
			<p>
				<strong>Seeders:</strong> %s<br />
				<strong>Leechers:</strong> %s
			</p>""" % tracker.get(file.get_hash()))
		self.w("""
			<p style="text-align: right;">
				<a href="http://download.ipfire.org/torrent/%s">Download</a>
			</p>""" % (file.name,))
		

class Content(web.Content):
	def __init__(self, name):
		web.Content.__init__(self, name)
	
	def content(self):
		self.w("<h3>IPFire Torrent Tracker</h3>")
		for t in torrent_files:
			b = TorrentBox(t)
			self.w(b())

Sidebar = web.Sidebar
