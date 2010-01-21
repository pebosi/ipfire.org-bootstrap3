#/usr/bin/python

import os.path
import simplejson

simplejson._default_decoder = simplejson.JSONDecoder(encoding="latin-1")

import tornado.locale
import tornado.options
import tornado.web

from handlers import *
from ui_modules import *

BASEDIR = os.path.join(os.path.dirname(__file__), "..")

tornado.locale.load_translations(os.path.join(BASEDIR, "translations"))
tornado.options.enable_pretty_logging()

class Application(tornado.web.Application):
	def __init__(self):
		settings = dict(
			cookie_secret = "aXBmaXJlY29va2llc2VjcmV0Cg==",
			#debug = True,
			gzip = True,
			template_path = os.path.join(BASEDIR, "templates"),
			ui_modules = {
				"Build"          : BuildModule,
				"Menu"           : MenuModule,
				"MenuItem"       : MenuItemModule,
				"NewsItem"       : NewsItemModule,
				"ReleaseItem"    : ReleaseItemModule,
				"SidebarBanner"  : SidebarBannerModule,
				"SidebarItem"    : SidebarItemModule,
				"SidebarRelease" : SidebarReleaseModule,
			},
			xsrf_cookies = True,
		)

		tornado.web.Application.__init__(self, **settings)

		self.settings["static_path"] = static_path = os.path.join(BASEDIR, "static")
		static_handlers = [
			(r"/static/(.*)", tornado.web.StaticFileHandler, dict(path = static_path)),
			(r"/(favicon\.ico)", tornado.web.StaticFileHandler, dict(path = static_path)),
			(r"/(robots\.txt)", tornado.web.StaticFileHandler, dict(path = static_path)),
		]

		self.add_handlers(r"www\.ipfire\.org", [
			# Entry sites that lead the user to index
			(r"/", MainHandler),
			(r"/[A-Za-z]{2}/?", MainHandler),
			#
			(r"/[A-Za-z]{2}/index", IndexHandler),
			(r"/[A-Za-z]{2}/news", NewsHandler),
			(r"/[A-Za-z]{2}/builds", BuildHandler),
			(r"/[A-Za-z]{2}/translations?", TranslationHandler),
			# Download sites
			(r"/[A-Za-z]{2}/downloads?", DownloadHandler),
			(r"/[A-Za-z]{2}/downloads?/all", DownloadAllHandler),
			(r"/[A-Za-z]{2}/downloads?/development", DownloadDevelopmentHandler),
			(r"/[A-Za-z]{2}/downloads?/torrents", DownloadTorrentHandler),
			# API
			(r"/api/cluster_info", ApiClusterInfoHandler),
			# Always the last rule
			(r"/[A-Za-z]{2}/(.*)", StaticHandler),
		] + static_handlers)

		# download.ipfire.org
		self.add_handlers(r"download\.ipfire\.org", [
			(r"/", MainHandler),
			(r"/[A-Za-z]{2}/index", DownloadHandler),
		] + static_handlers)

		# source.ipfire.org
		self.add_handlers(r"source\.ipfire\.org", [
			(r"/", MainHandler),
			(r"/[A-Za-z]{2}/index", SourceHandler),
		] + static_handlers)

		# torrent.ipfire.org
		self.add_handlers(r"torrent\.ipfire\.org", [
			(r"/", MainHandler),
			(r"/[A-Za-z]{2}/index", DownloadTorrentHandler),
		] + static_handlers)

		# tracker.ipfire.org
		self.add_handlers(r"tracker\.ipfire\.org", [
			(r"/", MainHandler),
			(r"/[A-Za-z]{2}/index", DownloadTorrentHandler),
		] + static_handlers)

		# ipfire.org
		self.add_handlers(r"ipfire\.org", [
			(r".*", tornado.web.RedirectHandler, { "url" : "http://www.ipfire.org" })
		])
