#!/usr/bin/python

import re
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


class TrackerBaseHandler(BaseHandler):
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
		msg = bencode({"failure reason" : error_message })
		self.finish(msg)


class TrackerAnnounceHandler(TrackerBaseHandler):
	def prepare(self):
		self.set_header("Content-Type", "text/plain")

	def get_ipv6_address(self, default_port):
		# Get the external IP address of the client.
		addr = self.get_remote_ip()

		if ":" in addr:
			return addr, default_port

		# IPv6
		ipv6 = self.get_argument("ipv6", None)
		if ipv6:
			port = default_port

			m = re.match("^\[(.*)\]\:(\d)$", ipv6)
			if m:
				ipv6, port = (m.group(1), m.group(2))

			return ipv6, port

		return None, None

	def get_ipv4_address(self, default_port):
		# Get the external IP address of the client.
		addr = self.get_remote_ip()

		if not ":" in addr:
			return addr, default_port

		# IPv4
		ipv4 = self.get_argument("ipv4", None)
		if ipv4:
			return ipv4, default_port

		ip = self.get_argument("ip", None)
		if ip:
			return ip, default_port

		return None, None

	def get_port(self):
		# Get the port and check it for sanity
		port = self.get_argument("port", None)

		try:
			port = int(port)

			if port < 0 or port > 65535:
				raise ValueError
		except (TypeError, ValueError):
			port = None

		return port

	def get(self):
		# Get the info hash
		info_hash = self.get_hexencoded_argument("info_hash")
		if not info_hash:
			self.send_tracker_error("Your client forgot to send your torrent's info_hash")
			return

		# Get the peer id
		peer_id = self.get_hexencoded_argument("peer_id")

		# Get the port and check it for sanity
		port = self.get_port()
		if not port:
			self.send_tracker_error("Invalid port number or port number missing")
			return

		addr_ipv6, port_ipv6 = self.get_ipv6_address(port)
		addr_ipv4, port_ipv4 = self.get_ipv4_address(port)

		# Handle events
		event = self.get_argument("event", None)
		if event:
			if not event in ("started", "stopped", "completed"):
				self.send_tracker_error("Got unknown event")
				return

			self.tracker.handle_event(event, peer_id, info_hash,
				address6=addr_ipv6, port6=port_ipv6, address4=addr_ipv4, port4=port_ipv4)

		peer_info = {
			"address6"   : addr_ipv6,
			"port6"      : port_ipv6,
			"address4"   : addr_ipv4,
			"port4"      : port_ipv4,
			"downloaded" : self.get_argument("downloaded", 0),
			"uploaded"   : self.get_argument("uploaded", 0),
			"left_data"  : self.get_argument("left", 0),
		}

		self.tracker.update_peer(peer_id, info_hash, **peer_info)

		no_peer_id = self.get_argument("no_peer_id", False)
		numwant = self.get_argument("numwant", self.tracker.numwant)

		peers = self.tracker.get_peers(info_hash, limit=numwant, no_peer_id=no_peer_id)

		response = bencode({
			"tracker id"   : self.tracker.tracker_id,
			"interval"     : self.tracker.interval,
			"min interval" : self.tracker.min_interval,
			"peers"        : peers,
			"complete"     : self.tracker.complete(info_hash),
			"incomplete"   : self.tracker.incomplete(info_hash),
		})
		self.finish(response)

	def on_finish(self):
		"""
			Cleanup after every request.
		"""
		self.tracker.cleanup_peers()


class TrackerScrapeHandler(TrackerBaseHandler):
	def get(self):
		info_hashes = self.get_hexencoded_argument("info_hash", all=True)

		response = self.tracker.scrape(info_hashes)

		self.finish(bencode(response))
