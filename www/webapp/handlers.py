#!/usr/bin/python

import datetime
import httplib
import mimetypes
import operator
import os
import re
import simplejson
import stat
import sqlite3
import time
import unicodedata
import urlparse

import tornado.database
import tornado.httpclient
import tornado.locale
import tornado.web

from banners import banners
from helpers import size, Item
from info import info
from mirrors import mirrors
from news import news
from releases import releases
from torrent import tracker, bencode, bdecode, decode_hex

import builds
import menu
import cluster
import markdown
#import uriel

class BaseHandler(tornado.web.RequestHandler):
	def get_user_locale(self):
		uri = self.request.uri.split("/")
		if len(uri) > 1:
			for lang in tornado.locale.get_supported_locales(None):
				if lang[:2] == uri[1]:
					return tornado.locale.get(lang)

	@property
	def render_args(self):
		return {
			"banner"    : banners.get(),
			"lang"      : self.locale.code[:2],
			"langs"     : [l[:2] for l in tornado.locale.get_supported_locales(None)],
			"lang_link" : self.lang_link,
			"link"      : self.link,
			"title"     : "no title given",
			"server"    : self.request.host.replace("ipfire", "<span>ipfire</span>"),
			"uri"       : self.request.uri,
			"year"      : time.strftime("%Y"),
		}

	def render(self, *args, **kwargs):
		nargs = self.render_args
		nargs.update(kwargs)
		nargs["hostname"] = self.request.host
		tornado.web.RequestHandler.render(self, *args, **nargs)

	def link(self, s):
		return "/%s/%s" % (self.locale.code[:2], s)
	
	def lang_link(self, lang):
		return "/%s/%s" % (lang, self.request.uri[4:])
	
	def get_error_html(self, status_code, **kwargs):
		if status_code in (404, 500):
			render_args = self.render_args
			render_args.update({
				"code"      : status_code,
				"exception" : kwargs.get("exception", None),
				"message"   : httplib.responses[status_code],
			})
			return self.render_string("error-%s.html" % status_code, **render_args)
		else:
			return tornado.web.RequestHandler.get_error_html(self, status_code, **kwargs)

	@property
	def hash_db(self):
		return self.application.hash_db

	@property
	def planet_db(self):
		return self.application.planet_db

	@property
	def user_db(self):
		return self.application.user_db


class MainHandler(BaseHandler):
	def get(self):
		lang = self.locale.code[:2]
		self.redirect("/%s/index" % (lang))


class DownloadHandler(BaseHandler):
	def get(self):
		self.render("downloads.html", release=releases.latest)


class DownloadAllHandler(BaseHandler):
	def get(self):
		self.render("downloads-all.html", releases=releases)


class DownloadDevelopmentHandler(BaseHandler):
	def get(self):
		self.render("downloads-development.html", releases=releases)


class DownloadTorrentHandler(BaseHandler):
	tracker_url = "http://tracker.ipfire.org:6969/stats?format=txt&mode=tpbs"

	@tornado.web.asynchronous
	def get(self):
		http = tornado.httpclient.AsyncHTTPClient()
		http.fetch(self.tracker_url, callback=self.async_callback(self.on_response))

	def on_response(self, response):
		torrents = releases.torrents
		hashes = {}
		if response.code == 200:
			for line in response.body.split("\n"):
				if not line: continue
				hash, seeds, peers = line.split(":")
				hash.lower()
				hashes[hash] = {
					"peers" : peers,
					"seeds" : seeds,
				}

		self.render("downloads-torrents.html",
			hashes=hashes,
			releases=torrents,
			request_time=response.request_time,
			tracker=urlparse.urlparse(response.request.url).netloc)


class DownloadMirrorHandler(BaseHandler):
	def get(self):
		self.render("downloads-mirrors.html", mirrors=mirrors)


class StaticHandler(BaseHandler):
	@property
	def static_path(self):
		return os.path.join(self.application.settings["template_path"], "static")

	@property
	def static_files(self):
		ret = []
		for filename in os.listdir(self.static_path):
			if filename.endswith(".html"):
				ret.append(filename)
		return ret

	def get(self, name=None):
		name = "%s.html" % name

		if not name in self.static_files:
			raise tornado.web.HTTPError(404)

		self.render("static/%s" % name)


class IndexHandler(BaseHandler):
	def get(self):
		self.render("index.html", news=news)


class NewsHandler(BaseHandler):
	def get(self):
		self.render("news.html", news=news)


class BuildHandler(BaseHandler):
	def prepare(self):
		self.builds = {
			"<12h" : [],
			">12h" : [],
			">24h" : [],
		}

		for build in builds.find():
			if (time.time() - float(build.get("date"))) < 12*60*60:
				self.builds["<12h"].append(build)
			elif (time.time() - float(build.get("date"))) < 24*60*60:
				self.builds[">12h"].append(build)
			else:
				self.builds[">24h"].append(build)

		for l in self.builds.values():
			l.sort()

	def get(self):
		self.render("builds.html", builds=self.builds)


class UrielBaseHandler(BaseHandler):
	#db = uriel.Database()
	pass

class UrielHandler(UrielBaseHandler):
	def get(self):
		pass


class SourceHandler(BaseHandler):
	def get(self):
		source_path = "/srv/sources"
		fileobjects = []

		for dir, subdirs, files in os.walk(source_path):
			if not files:
				continue
			for file in files:
				if file in [f["name"] for f in fileobjects]:
					continue

				hash = self.hash_db.get_hash(os.path.join(dir, file))

				if not hash:
					hash = "0000000000000000000000000000000000000000"

				fileobjects.append({
					"dir"  : dir[len(source_path)+1:],
					"name" : file,
					"hash" : hash,
					"size" : size(os.path.getsize(os.path.join(source_path, dir, file))),
				})

		fileobjects.sort(key=operator.itemgetter("name"))

		self.render("sources.html", files=fileobjects)


class SourceDownloadHandler(BaseHandler):
	def head(self, path):
		self.get(path, include_body=False)

	def get(self, path, include_body=True):
		source_path = "/srv/sources"

		path = os.path.abspath(os.path.join(source_path, path[1:]))

		if not path.startswith(source_path):
			raise tornado.web.HTTPError(403)
		if not os.path.exists(path):
			raise tornado.web.HTTPError(404)

		stat_result = os.stat(path)
		modified = datetime.datetime.fromtimestamp(stat_result[stat.ST_MTIME])

		self.set_header("Last-Modified", modified)
		self.set_header("Content-Length", stat_result[stat.ST_SIZE])

		mime_type, encoding = mimetypes.guess_type(path)
		if mime_type:
			self.set_header("Content-Type", mime_type)

		hash = self.hash_db.get_hash(path)
		if hash:
			self.set_header("X-Hash-Sha1", "%s" % hash)

		if not include_body:
			return
		file = open(path, "r")
		try:
			self.write(file.read())
		finally:
			file.close()


class DownloadFileHandler(BaseHandler):
	def get(self, path):
		for mirror in mirrors.with_file(path):
			if not mirror.reachable:
				continue

			self.redirect(mirror.url + path)
			return

		raise tornado.web.HTTPError(404)

	def get_error_html(self, status_code, **kwargs):
		return tornado.web.RequestHandler.get_error_html(self, status_code, **kwargs)


class RSSHandler(BaseHandler):
	def get(self, lang):
		items = []
		for item in news.get(15):
			item = Item(**item.args.copy())
			for attr in ("subject", "content"):
				if type(item[attr]) == type({}):
					item[attr] = item[attr][lang]
			items.append(item)

		self.set_header("Content-Type", "application/rss+xml")
		self.render("rss.xml", items=items, lang=lang)


<<<<<<< HEAD
class TrackerBaseHandler(tornado.web.RequestHandler):
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

		peer = {
			"id" : self.get_hexencoded_argument("peer_id"),
			"ip" : self.get_argument("ip", None),
			"port" : self.get_argument("port", None),
			"downloaded" : self.get_argument("downloaded", 0),
			"uploaded" : self.get_argument("uploaded", 0),
			"left" : self.get_argument("left", 0),
		}

		event = self.get_argument("event", "")
		if not event in ("started", "stopped", "completed", ""):
			self.send_tracker_error("Got unknown event")
			return

		if peer["ip"]:
			if peer["ip"].startswith("10.") or \
				peer["ip"].startswith("172.") or \
				peer["ip"].startswith("192.168."):
				peer["ip"] = self.request.remote_ip

		if peer["port"]:
			peer["port"] = int(peer["port"])

			if peer["port"] < 0 or peer["port"] > 65535:
				self.send_tracker_error("Port number is not in valid range")
				return

		eventhandlers = {
			"started" : tracker.event_started,
			"stopped" : tracker.event_stopped,
			"completed" : tracker.event_completed,
		}

		if event:
			eventhandlers[event](info_hash, peer["id"])

		tracker.update(hash=info_hash, **peer)

		no_peer_id = self.get_argument("no_peer_id", False)
		numwant = self.get_argument("numwant", tracker.numwant)

		self.write(bencode({
			"tracker id" : tracker.id,
			"interval" : tracker.interval,
			"min interval" : tracker.min_interval,
			"peers" : tracker.get_peers(info_hash, limit=numwant,
				random=True, no_peer_id=no_peer_id),
			"complete" : tracker.complete(info_hash),
			"incomplete" : tracker.incomplete(info_hash),
		}))
		self.finish()


class TrackerScrapeHandler(TrackerBaseHandler):
	def get(self):
		info_hashes = self.get_hexencoded_argument("info_hash", all=True)

		self.write(bencode(tracker.scrape(hashes=info_hashes)))
		self.finish()
=======
class PlanetBaseHandler(BaseHandler):
	@property
	def db(self):
		return self.application.planet_db


class PlanetMainHandler(PlanetBaseHandler):
	def get(self):
		authors = self.db.query("SELECT DISTINCT author_id FROM entries")
		authors = [a["author_id"] for a in authors]

		users = []
		for user in self.user_db.users:
			if user.id in authors:
				users.append(user)

		entries = self.db.query("SELECT * FROM entries "
			"ORDER BY published DESC LIMIT 3")
		
		for entry in entries:
			entry.author = self.user_db.get_user_by_id(entry.author_id)

		self.render("planet-main.html", entries=entries, authors=users)


class PlanetUserHandler(PlanetBaseHandler):
	def get(self, user):
		if not user in [u.name for u in self.user_db.users]:
			raise tornado.web.HTTPError(404, "User is unknown")

		user = self.user_db.get_user_by_name(user)

		entries = self.db.query("SELECT * FROM entries "
			"WHERE author_id = '%s' ORDER BY published DESC" % (user.id))

		self.render("planet-user.html", entries=entries, user=user)


class PlanetPostingHandler(PlanetBaseHandler):
	def get(self, slug):
		entry = self.db.get("SELECT * FROM entries WHERE slug = %s", slug)

		if not entry:
			raise tornado.web.HTTPError(404)

		user = self.user_db.get_user_by_id(entry.author_id)
		entry.author = user

		self.render("planet-posting.html", entry=entry, user=user)
>>>>>>> planet
