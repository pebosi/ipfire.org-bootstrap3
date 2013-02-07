#!/usr/bin/python

import tornado.web

from backend.tracker import bencode, bdecode, decode_hex
from handlers_base import *


class TrackerIndexHandler(BaseHandler):
	def get(self):
		releases = self.releases.get_all()

		limit = 5
		releases = releases[:limit]

		self.render("tracker-torrents.html", releases=releases)


class TrackerDetailHandler(BaseHandler):
	def get(self, torrent_hash):
		file = self.releases.get_file_for_torrent_hash(torrent_hash)

		if not file:
			raise tornado.web.HTTPError(404, "Could not find torrent file for hash: %s" % torrent_hash)

		peers = self.tracker.get_peers(torrent_hash)
		seeds = self.tracker.get_seeds(torrent_hash)

		self.render("tracker-torrent-detail.html", release=file.release,
			file=file, peers=peers, seeds=seeds)


class TrackerDownloadHandler(BaseHandler):
	def get(self, torrent_hash):
		file = self.releases.get_file_for_torrent_hash(torrent_hash)

		if not file:
			raise tornado.web.HTTPError(404, "Could not find torrent file for hash: %s" % torrent_hash)

		# Redirect the user to the download redirector.
		self.redirect("http://downloads.ipfire.org/%s.torrent" % file.filename)


#class TrackerTorrentsHandler(BaseHandler):
#	@property
#	def tracker(self):
#		return self.tracker
#
#	def get(self):		
#		releases = []
#
#		for release in self.releases.get_all():
#			if not release.torrent_hash:
#				continue
#
#			release.torrent_hash = release.torrent_hash.lower()
#
#			release.torrent_peers = self.tracker.incomplete(release.torrent_hash)
#			release.torrent_seeds = self.tracker.complete(release.torrent_hash)
#
#			releases.append(release)
#
#		self.render("tracker-torrents.html", releases=releases)


class TrackerBaseHandler(tornado.web.RequestHandler):
	@property
	def tracker(self):
		return backend.Tracker()

	def get_hexencoded_argument(self, name, all=False):
		try:
			arguments = self.request.arguments[name]
		except KeyError:
			return None

		arguments_new = []
		for argument in arguments:
			arguments_new.append(decode_hex(argument))

		arguments = arguments_new

		if all:
			return arguments

		return arguments[0]

	def send_tracker_error(self, error_message):
		self.write(bencode({"failure reason" : error_message }))
		self.finish()


class TrackerAnnounceHandler(TrackerBaseHandler):
	def get(self):
		self.set_header("Content-Type", "text/plain")

		info_hash = self.get_hexencoded_argument("info_hash")
		if not info_hash:
			self.send_tracker_error("Your client forgot to send your torrent's info_hash.")
			return

		# Fix for clients behind a proxy that sends "X-Forwarded-For".
		ip_addr = self.request.remote_ip.split(", ")
		if ip_addr:
			ip_addr = ip_addr[-1]

		peer = {
			"id" : self.get_hexencoded_argument("peer_id"),
			"ip" : ip_addr,
			"port" : self.get_argument("port", None),
			"downloaded" : self.get_argument("downloaded", 0),
			"uploaded" : self.get_argument("uploaded", 0),
			"left" : self.get_argument("left", 0),
		}

		event = self.get_argument("event", "")
		if not event in ("started", "stopped", "completed", ""):
			self.send_tracker_error("Got unknown event")
			return

		if peer["port"]:
			peer["port"] = int(peer["port"])

			if peer["port"] < 0 or peer["port"] > 65535:
				self.send_tracker_error("Port number is not in valid range")
				return

		eventhandlers = {
			"started" : self.tracker.event_started,
			"stopped" : self.tracker.event_stopped,
			"completed" : self.tracker.event_completed,
		}

		if event:
			eventhandlers[event](info_hash, peer["id"])

		self.tracker.update(hash=info_hash, **peer)

		no_peer_id = self.get_argument("no_peer_id", False)
		numwant = self.get_argument("numwant", self.tracker.numwant)

		self.write(bencode({
			"tracker id" : self.tracker.id,
			"interval" : self.tracker.interval,
			"min interval" : self.tracker.min_interval,
			"peers" : self.tracker.get_peers(info_hash, limit=numwant,
				random=True, no_peer_id=no_peer_id),
			"complete" : self.tracker.complete(info_hash),
			"incomplete" : self.tracker.incomplete(info_hash),
		}))
		self.finish()


class TrackerScrapeHandler(TrackerBaseHandler):
	def get(self):
		info_hashes = self.get_hexencoded_argument("info_hash", all=True)

		self.write(bencode(self.tracker.scrape(hashes=info_hashes)))
		self.finish()
