#/usr/bin/python

import os.path

import tornado.locale
import tornado.options
import tornado.web

from .handlers import *
from .ui_modules import *

BASEDIR = os.path.join(os.path.dirname(__file__), "..")

tornado.locale.load_translations(os.path.join(BASEDIR, "translations"))
tornado.options.enable_pretty_logging()

class Application(tornado.web.Application):
	def __init__(self):
		handlers = [
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
		]

		settings = dict(
			cookie_secret = "aXBmaXJlY29va2llc2VjcmV0Cg==",
			#debug = True,
			gzip = True,
			static_path = os.path.join(BASEDIR, "static"),
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
		tornado.web.Application.__init__(self, handlers, **settings)

		# ipfire.org
		self.add_handlers("ipfire.org", [
			(r"/", tornado.web.RedirectHandler, { "url" : "http://www.ipfire.org" })
		])

		# download.ipfire.org
		self.add_handlers("download.ipfire.org", [
			(r"/", MainHandler),
			(r"/[A-Za-z]{2}/index", DownloadHandler),
		])

		# source.ipfire.org
		self.add_handlers("source.ipfire.org", [
			(r"/", MainHandler),
			(r"/[A-Za-z]{2}/index", SourceHandler),
		])

		# torrent.ipfire.org
		self.add_handlers("torrent.ipfire.org", [
			(r"/", MainHandler),
			(r"/[A-Za-z]{2}/index", DownloadTorrentHandler),
		])

		# tracker.ipfire.org
		self.add_handlers("tracker.ipfire.org", [
			(r"/", MainHandler),
			(r"/[A-Za-z]{2}/index", DownloadTorrentHandler),
		])
