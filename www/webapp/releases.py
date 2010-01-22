#!/usr/bin/python

import simplejson

from helpers import Item, _stringify

class ReleaseItem(Item):
	options = {
		"iso" : {
			"prio" : 10,
			"desc" : "Installable CD image",
			"url"  : "http://download.ipfire.org/iso/",
			"rem"  : "Use this image to burn a CD and install IPFire from it.",
		},
		"torrent" : {
			"prio" : 20,
			"desc" : "Torrent file",
			"url"  : "http://download.ipfire.org/torrent/",
			"rem"  : "Download the CD image from the torrent network.",
		},
		"alix" : {
			"prio" : 40,
			"desc" : "Alix image",
			"url"  : "http://download.ipfire.org/iso/",
			"rem"  : "An image that is meant to run on embedded devices.",
		},
		"usbfdd" : {
			"prio" : 30,
			"desc" : "USB FDD Image",
			"url"  : "http://download.ipfire.org/iso/",
			"rem"  : "Install IPFire from a floppy-formated USB key.",
		},
		"usbhdd" : {
			"prio" : 30,
			"desc" : "USB HDD Image",
			"url"  : "http://download.ipfire.org/iso/",
			"rem"  : "If the floppy image doesn't work, use this image instead.",
		},
		"xen" : {
			"prio" : 50,
			"desc" : "Pregenerated Xen Image",
			"url"  : "http://download.ipfire.org/iso/",
			"rem"  : "A ready-to-run image for Xen.",
		},
	}

	@property
	def downloads(self):
		ret = []
		for fileitem in self.args["files"]:
			filetype = fileitem["type"]
			ret.append(Item(
				desc = self.options[filetype]["desc"],
				file = fileitem["name"],
				hash = fileitem.get("hash", None),
				prio = self.options[filetype]["prio"],
				rem  = self.options[filetype]["rem"],
				sha1 = fileitem.get("sha1", None),
				type = filetype,
				url  = self.options[filetype]["url"] + fileitem["name"],
			))

		ret.sort(lambda a, b: cmp(a.prio, b.prio))
		return ret
		
		for option in self.options.keys():
			if not self.args["files"].has_key(option):
				continue

			ret.append(Item(
				desc = self.options[option]["desc"],
				file = self.args["files"][option],
				prio = self.options[option]["prio"],
				type = option,
				url = self.options[option]["url"] + self.args["files"][option],
			))

		ret.sort(lambda a, b: cmp(a.prio, b.prio))
		return ret

	@property
	def iso(self):
		for download in self.downloads:
			if download.type == "iso":
				return download

	@property
	def torrent(self):
		for download in self.downloads:
			if download.type == "torrent":
				return download

	@property
	def stable(self):
		return self.status == "stable"

	@property
	def development(self):
		return self.status == "development"


class Releases(object):
	def __init__(self, filename="releases.json"):
		self.items = []

		if filename:
			self.load(filename)
	
	def load(self, filename):
		f = open(filename)
		data = f.read()
		f.close()
		
		for item in simplejson.loads(data):
			self.items.append(ReleaseItem(**_stringify(item)))

	@property
	def all(self):
		return self.items

	@property
	def online(self):
		ret = []
		for item in self.all:
			if item.online:
				ret.append(item)
		return ret

	@property
	def offline(self):
		ret = []
		for item in self.all:
			if not item.online:
				ret.append(item)
		return ret

	@property
	def latest(self):
		if self.stable:
			return self.stable[0]

	@property
	def latest_devel(self):
		if self.development:
			return self.development[0]

	@property
	def stable(self):
		ret = []
		for item in self.online:
			if item.stable:
				ret.append(item)
		return ret

	@property
	def development(self):
		ret = []
		for item in self.online:
			if item.development:
				ret.append(item)
		return ret

	@property
	def torrents(self):
		ret = []
		for item in self.online:
			if item.torrent:
				ret.append(item)
		return ret


releases = Releases("releases.json")

if __name__ == "__main__":
	r = Releases()

	print r.stable
	print r.development
	print r.latest
	print r.online
	print r.offline
