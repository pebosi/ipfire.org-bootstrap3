#/usr/bin/python

import logging
import os.path
import simplejson
import tornado.httpserver
import tornado.locale
import tornado.options
import tornado.web

import backend

from handlers import *
from ui_modules import *

BASEDIR = os.path.join(os.path.dirname(__file__), "..")

tornado.locale.load_translations(os.path.join(BASEDIR, "translations"))

class Application(tornado.web.Application):
	def __init__(self):
		settings = dict(
			cookie_secret = "aXBmaXJlY29va2llc2VjcmV0Cg==",
			debug = False,
			gzip = True,
			login_url = "/login",
			template_path = os.path.join(BASEDIR, "templates"),
			ui_modules = {
				"Menu"           : MenuModule,
				"MirrorItem"     : MirrorItemModule,
				"NewsItem"       : NewsItemModule,
				"NewsLine"       : NewsLineModule,
				"PlanetEntry"    : PlanetEntryModule,
				"ReleaseItem"    : ReleaseItemModule,
				"SidebarBanner"  : SidebarBannerModule,
				"SidebarRelease" : SidebarReleaseModule,
				"StasyTable"     : StasyTableModule,
				"StasyDeviceTable" : StasyDeviceTableModule,
				"TrackerPeerList": TrackerPeerListModule,
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

		self.add_handlers(r"(dev|www)\.ipfire\.(at|org)", [
			# Entry site that lead the user to index
			(r"/", IndexHandler),
			(r"/index\.?(s?html?)?", RootHandler),

			# Handle news items
			(r"/news", NewsIndexHandler),
			(r"/news/(.*)", NewsItemHandler),
			(r"/author/(.*)", NewsAuthorHandler),

			# Download sites
			(r"/downloads?", DownloadHandler),

			# RSS feed
			(r"/news.rss", RSSNewsHandler),

			# Redirection for bookmarks, etc.
			(r"/(de|en)/(.*)", LangCompatHandler)

		] + static_handlers + [
			# Always the last rule
			(r"/(.*)", StaticHandler),
		])

		# downloads.ipfire.org
		self.add_handlers(r"downloads?\.ipfire\.org", [
			(r"/", DownloadsIndexHandler),
			(r"/latest", DownloadsLatestHandler),
			(r"/release/([0-9]+)", DownloadsReleaseHandler),
			(r"/older", DownloadsOlderHandler),
			(r"/development", DownloadsDevelopmentHandler),
			(r"/mirrors", tornado.web.RedirectHandler, { "url" : "http://mirrors.ipfire.org/" }),
			(r"/source", tornado.web.RedirectHandler, { "url" : "http://source.ipfire.org/" }),
		] + static_handlers + [
			(r"/(.*)", DownloadFileHandler),
		])

		# mirrors.ipfire.org
		self.add_handlers(r"mirrors\.ipfire\.org", [
			(r"/", MirrorIndexHandler),
			(r"/mirror/([0-9]+)", MirrorItemHandler),
		] + static_handlers)

		# planet.ipfire.org
		self.add_handlers(r"planet\.ipfire\.org", [
			(r"/", PlanetMainHandler),
			(r"/post/([A-Za-z0-9_-]+)", PlanetPostingHandler),
			(r"/user/([a-z0-9_-]+)", PlanetUserHandler),

			# RSS
			(r"/rss", RSSPlanetAllHandler),
			(r"/user/([a-z0-9_-]+)/rss", RSSPlanetUserHandler),
		] + static_handlers)

		# stasy.ipfire.org
		self.add_handlers(r"(fireinfo|stasy)\.ipfire\.org", [
			(r"/", StasyIndexHandler),
			(r"/profile/([a-z0-9]{40})", StasyProfileDetailHandler),
			(r"/vendor/(pci|usb)/([0-9a-f]{4})", StasyStatsVendorDetail),
			(r"/model/(pci|usb)/([0-9a-f]{4})/([0-9a-f]{4})", StasyStatsModelDetail),

			# Stats handlers			
			(r"/stats", StasyStatsHandler),
			(r"/stats/cpus", StasyStatsCPUHandler),
			(r"/stats/cpuflags", StasyStatsCPUFlagsHandler),
			(r"/stats/geo", StasyStatsGeoHandler),
			(r"/stats/memory", StasyStatsMemoryHandler),
			(r"/stats/network", StasyStatsNetworkHandler),
			(r"/stats/oses", StasyStatsOSesHandler),
			(r"/stats/virtual", StasyStatsVirtualHandler),
		] + static_handlers)

		# i-use.ipfire.org
		self.add_handlers(r"i-use\.ipfire\.org", [
			(r"/profile/([a-f0-9]{40})/([0-9]+).png", IUseImage),
		])

		# tracker.ipfire.org
		self.add_handlers(r"(torrent|tracker)\.ipfire\.org", [
			(r"/", TrackerIndexHandler),
			(r"/a.*", TrackerAnnounceHandler),
			(r"/scrape", TrackerScrapeHandler),
			(r"/torrent/([0-9a-f]+)", TrackerDetailHandler),
		] + static_handlers)

		# admin.ipfire.org
		self.add_handlers(r"admin\.ipfire\.org", [
			(r"/", AdminIndexHandler),
			(r"/login", AdminLoginHandler),
			(r"/logout", AdminLogoutHandler),
			# Accounts
			(r"/accounts", AdminAccountsHandler),
			#(r"/accounts/delete/([0-9]+)", AdminAccountsDeleteHandler),
			#(r"/accounts/edit/([0-9]+)", AdminAccountsEditHandler),
			# Planet
			(r"/planet", AdminPlanetHandler),
			(r"/planet/compose", AdminPlanetComposeHandler),
			(r"/planet/edit/([0-9]+)", AdminPlanetEditHandler),
			# Mirrors
			(r"/mirrors", AdminMirrorsHandler),
			(r"/mirrors/create", AdminMirrorsCreateHandler),
			(r"/mirrors/delete/([0-9]+)", AdminMirrorsDeleteHandler),
			(r"/mirrors/edit/([0-9]+)", AdminMirrorsEditHandler),
			(r"/mirrors/details/([0-9]+)", AdminMirrorsDetailsHandler),
			(r"/mirrors/update", AdminMirrorsUpdateHandler),
			# Fireinfo
			(r"/fireinfo/stats", AdminFireinfoStatsHandler),
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
	def ioloop(self):
		return tornado.ioloop.IOLoop.instance()

	def shutdown(self, *args):
		logging.debug("Caught shutdown signal")
		self.ioloop.stop()

		self.__running = False

	def run(self, port=8001):
		logging.debug("Going to background")

		http_server = tornado.httpserver.HTTPServer(self, xheaders=True)

		# If we are not running in debug mode, we can actually run multiple
		# frontends to get best performance out of our service.
		if not self.settings["debug"]:
			http_server.bind(port)
			http_server.start(num_processes=4)
		else:
			http_server.listen(port)
		
		# All requests should be done after 30 seconds or they will be killed.
		self.ioloop.set_blocking_log_threshold(30)

		self.ioloop.start()

	def reload(self):
		logging.debug("Caught reload signal")
