#/usr/bin/python

import logging
import multiprocessing
import os.path
import simplejson
import tornado.httpserver
import tornado.locale
import tornado.web

from tornado.options import options

import backend

from handlers import *
from ui_modules import *

BASEDIR = os.path.join(os.path.dirname(__file__), "..")

# Load translations.
tornado.locale.load_gettext_translations(os.path.join(BASEDIR, "translations"), "webapp")

class Application(tornado.web.Application):
	def __init__(self):
		settings = dict(
			cookie_secret = "aXBmaXJlY29va2llc2VjcmV0Cg==",
			debug = options.debug,
			gzip = True,
			login_url = "/login",
			template_path = os.path.join(BASEDIR, "templates"),
			ui_methods = {
				"format_month_name" : self.format_month_name,
			},
			ui_modules = {
				"Advertisement"  : AdvertisementModule,
				"DonationBox"    : DonationBoxModule,
				"DownloadButton" : DownloadButtonModule,
				"Menu"           : MenuModule,
				"MirrorItem"     : MirrorItemModule,
				"MirrorsTable"   : MirrorsTableModule,
				"NewsItem"       : NewsItemModule,
				"NewsLine"       : NewsLineModule,
				"NewsTable"      : NewsTableModule,
				"NewsYearNavigation": NewsYearNavigationModule,
				"PlanetEntry"    : PlanetEntryModule,
				"ReleaseItem"    : ReleaseItemModule,
				"SidebarBanner"  : SidebarBannerModule,
				"SidebarRelease" : SidebarReleaseModule,
				"StasyTable"     : StasyTableModule,
				"StasyCPUCoreTable" : StasyCPUCoreTableModule,
				"StasyDeviceTable" : StasyDeviceTableModule,
				"StasyGeoTable"  : StasyGeoTableModule,
				"TrackerPeerList": TrackerPeerListModule,
				"Wish"           : WishModule,
				"Wishlist"       : WishlistModule,
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
			(r"/news/year/([0-9]*)", NewsYearHandler),
			(r"/news/(.*)", NewsItemHandler),
			(r"/author/(.*)", NewsAuthorHandler),

			# Download sites
			(r"/download", DownloadHandler),
			(r"/downloads", tornado.web.RedirectHandler, { "url" : "/download" }),

			# Handle old pages that have moved elsewhere
			(r"/screenshots", tornado.web.RedirectHandler, { "url" : "/about" }),
			(r"/about", tornado.web.RedirectHandler, { "url" : "/features" }),
			(r"/support", tornado.web.RedirectHandler, { "url" : "/getinvolved" }),

			(r"/donate", tornado.web.RedirectHandler, { "url" : "/donation" }),

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
			(r"/download-splash", DownloadSplashHandler),
		] + static_handlers + [
			(r"/(iso|torrent)/(.*)", DownloadCompatHandler),
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
			(r"/search", PlanetSearchHandler),
			(r"/year/(\d+)", PlanetYearHandler),

			# API
			(r"/api/planet/search/autocomplete", PlanetAPISearchAutocomplete),

			# RSS
			(r"/rss", RSSPlanetAllHandler),
			(r"/user/([a-z0-9_-]+)/rss", RSSPlanetUserHandler),
			(r"/news.rss", tornado.web.RedirectHandler, { "url" : "/rss" }),
		] + static_handlers)

		# stasy.ipfire.org
		self.add_handlers(r"fireinfo\.ipfire\.org", [
			(r"/", StasyIndexHandler),
			(r"/profile/([a-z0-9]{40})", StasyProfileDetailHandler),
			(r"/vendor/(pci|usb)/([0-9a-f]{4})", StasyStatsVendorDetail),
			(r"/model/(pci|usb)/([0-9a-f]{4})/([0-9a-f]{4})", StasyStatsModelDetail),

			# Send profiles.
			(r"/send/([a-z0-9]+)", StasyProfileSendHandler),

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
			(r"/announce.*", TrackerAnnounceHandler),
			(r"/scrape", TrackerScrapeHandler),
			(r"/torrent/([0-9a-f]+)", TrackerDetailHandler),
			(r"/([0-9a-f]{40})", TrackerDetailHandler),
			(r"/([0-9a-f]{40})/download", TrackerDownloadHandler),
		] + static_handlers)

		# boot.ipfire.org
		BOOT_STATIC_PATH = os.path.join(self.settings["static_path"], "netboot")
		self.add_handlers(r"boot\.ipfire\.org", [
			(r"/", tornado.web.RedirectHandler, { "url" : "http://www.ipfire.org/download" }),

			# Configurations
			(r"/menu.gpxe", MenuGPXEHandler),
			(r"/menu.cfg", MenuCfgHandler),

			# Static files
			(r"/(boot\.png|premenu\.cfg|pxelinux\.0|menu\.c32|vesamenu\.c32)",
				tornado.web.StaticFileHandler, { "path" : BOOT_STATIC_PATH }),
		])

		# nopaste.ipfire.org
		self.add_handlers(r"nopaste\.ipfire\.org", [
			(r"/", NopasteIndexHandler),
			(r"/([\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12})", NopasteEntryHandler),
		] + static_handlers)

		# wishlist.ipfire.org
		self.add_handlers(r"wishlist\.ipfire\.org", [
			(r"/", WishlistIndexHandler),
			(r"/closed", WishlistClosedHandler),
			(r"/wish/(.*)/donate", WishDonateHandler),
			(r"/wish/(.*)", WishHandler),
			(r"/terms", WishlistTermsHandler),
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
			# Downloads
			(r"/downloads", AdminDownloadsHandler),
			(r"/downloads/mirrors", AdminDownloadsMirrorsHandler),
			# API
			(r"/api/planet/search/autocomplete", PlanetAPISearchAutocomplete),
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

		num_processes = multiprocessing.cpu_count() / 2

		# If we are not running in debug mode, we can actually run multiple
		# frontends to get best performance out of our service.
		if not self.settings["debug"]:
			http_server.bind(port)
			http_server.start(num_processes=num_processes)
		else:
			http_server.listen(port)
		
		# All requests should be done after 30 seconds or they will be killed.
		self.ioloop.set_blocking_log_threshold(30)

		self.ioloop.start()

	def reload(self):
		logging.debug("Caught reload signal")

	def format_month_name(self, handler, month):
		_ = handler.locale.translate

		if month == 1:
			return _("January")
		elif month == 2:
			return _("February")
		elif month == 3:
			return _("March")
		elif month == 4:
			return _("April")
		elif month == 5:
			return _("May")
		elif month == 6:
			return _("June")
		elif month == 7:
			return _("July")
		elif month == 8:
			return _("August")
		elif month == 9:
			return _("September")
		elif month == 10:
			return _("October")
		elif month == 11:
			return _("November")
		elif month == 12:
			return _("December")

		return month
