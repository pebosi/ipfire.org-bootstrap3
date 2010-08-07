#/usr/bin/python

import logging
import os.path
import simplejson

import tornado.httpserver
import tornado.locale
import tornado.options
import tornado.web

import datastore

from handlers import *
from ui_modules import *

BASEDIR = os.path.join(os.path.dirname(__file__), "..")

tornado.locale.load_translations(os.path.join(BASEDIR, "translations"))

class Application(tornado.web.Application):
	def __init__(self):
		settings = dict(
			cookie_secret = "aXBmaXJlY29va2llc2VjcmV0Cg==",
			#debug = True,
			gzip = True,
			login_url = "/login",
			template_path = os.path.join(BASEDIR, "templates"),
			ui_modules = {
				"Build"          : BuildModule,
				"Menu"           : MenuModule,
				"MenuItem"       : MenuItemModule,
				"NewsItem"       : NewsItemModule,
				"PlanetEntry"    : PlanetEntryModule,
				"ReleaseItem"    : ReleaseItemModule,
				"SidebarBanner"  : SidebarBannerModule,
				"SidebarItem"    : SidebarItemModule,
				"SidebarRelease" : SidebarReleaseModule,
			},
			xsrf_cookies = True,
		)

		tornado.web.Application.__init__(self, **settings)

		self.ds = datastore.DataStore(self)

		self.settings["static_path"] = static_path = os.path.join(BASEDIR, "static")
		static_handlers = [
			(r"/static/(.*)", tornado.web.StaticFileHandler, dict(path = static_path)),
			(r"/(favicon\.ico)", tornado.web.StaticFileHandler, dict(path = static_path)),
			(r"/(robots\.txt)", tornado.web.StaticFileHandler, dict(path = static_path)),
		]

		self.add_handlers(r"(dev|www)\.ipfire\.(at|org)", [
			# Entry sites that lead the user to index
			(r"/", MainHandler),
			(r"/[A-Za-z]{2}/?", MainHandler),
			#
			(r"/[A-Za-z]{2}/index", IndexHandler),
			(r"/[A-Za-z]{2}/news", NewsHandler),
			(r"/[A-Za-z]{2}/builds", BuildHandler),
			# Download sites
			(r"/[A-Za-z]{2}/downloads?", DownloadHandler),
			(r"/[A-Za-z]{2}/downloads?/all", DownloadAllHandler),
			(r"/[A-Za-z]{2}/downloads?/development", DownloadDevelopmentHandler),
			(r"/[A-Za-z]{2}/downloads?/mirrors", DownloadMirrorHandler),
			(r"/[A-Za-z]{2}/downloads?/torrents", DownloadTorrentHandler),
			# RSS feed
			(r"/([A-Za-z]{2})/news.rss", RSSHandler),
			(r"/data/feeds/main-([A-Za-z]{2}).rss", RSSHandler),
			# Always the last rule
			(r"/[A-Za-z]{2}/(.*)", StaticHandler),
		] + static_handlers)

		# download.ipfire.org
		self.add_handlers(r"download\.ipfire\.org", [
			(r"/", tornado.web.RedirectHandler, { "url" : "http://www.ipfire.org/" }),
			(r"/(favicon\.ico)", tornado.web.StaticFileHandler, dict(path = static_path)),
			(r"/(.*)", DownloadFileHandler),
		])

		# planet.ipfire.org
		self.add_handlers(r"planet\.ipfire\.org", [
			(r"/", MainHandler),
			(r"/[A-Za-z]{2}/?", MainHandler),
			(r"/[A-Za-z]{2}/index", PlanetMainHandler),
			(r"/post/([A-Za-z0-9_-]+)", PlanetPostingHandler),
			(r"/user/([a-z0-9]+)", PlanetUserHandler),
		] + static_handlers)

		# source.ipfire.org
		self.add_handlers(r"source\.ipfire\.org", [
			(r"/", MainHandler),
			(r"/[A-Za-z]{2}/?", MainHandler),
			(r"/[A-Za-z]{2}/index", SourceHandler),
			(r"(/source.*|/toolchains/.*)", SourceDownloadHandler),
		] + static_handlers)

		# torrent.ipfire.org
		self.add_handlers(r"torrent\.ipfire\.org", [
			(r"/", MainHandler),
			(r"/[A-Za-z]{2}/?", MainHandler),
			(r"/[A-Za-z]{2}/index", DownloadTorrentHandler),
		] + static_handlers)

		# tracker.ipfire.org
		self.add_handlers(r"tracker\.ipfire\.org", [
			(r"/", MainHandler),
			(r"/[A-Za-z]{2}/?", MainHandler),
			(r"/[A-Za-z]{2}/index", DownloadTorrentHandler),
			(r"/a.*", TrackerAnnounceHandler),
			(r"/scrape", TrackerScrapeHandler),
		] + static_handlers)

		# admin.ipfire.org
		self.add_handlers(r"admin\.ipfire\.org", [
			(r"/", AdminIndexHandler),
			(r"/login", AuthLoginHandler),
			(r"/logout", AuthLogoutHandler),
			# Accounts
			(r"/accounts", AdminAccountsHandler),
			(r"/accounts/edit/([0-9]+)", AdminAccountsEditHandler),
			# Planet
			(r"/planet", AdminPlanetHandler),
			(r"/planet/compose", AdminPlanetComposeHandler),
			(r"/planet/edit/([0-9]+)", AdminPlanetEditHandler),
			# API
			(r"/api/planet/render", AdminApiPlanetRenderMarkupHandler)
		] + static_handlers)

		# ipfire.org
		self.add_handlers(r".*", [
			(r".*", tornado.web.RedirectHandler, { "url" : "http://www.ipfire.org" })
		])

		logging.info("Successfully initialied application")

		self.__running = True

	def __del__(self):
		logging.info("Shutting down application")

	@property
	def db(self):
		return self.ds.db

	@property
	def ioloop(self):
		return tornado.ioloop.IOLoop.instance()

	def stop(self, *args):
		logging.debug("Caught shutdown signal")
		self.ioloop.stop()

		self.__running = False

	def run(self, port=8001):
		logging.debug("Going to background")

		http_server = tornado.httpserver.HTTPServer(self, xheaders=True)
		http_server.listen(port)

		self.ioloop.start()

		while self.__running:
			time.sleep(1)

			self.ds.trigger()

	def reload(self):
		logging.debug("Caught reload signal")

		self.ds.reload()
