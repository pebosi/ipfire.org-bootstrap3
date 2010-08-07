#!/usr/bin/python

import banners
#import builds
#import info
import menu
#import mirrors
import news
import releases
import tracker

from connections import *

class Databases(object):
	def __init__(self, application):
		self.application = application

		self.webapp = WebappConnection()

		self.config = self.webapp
		self.hashes = HashConnection()
		self.mirrors = self.webapp
		self.planet = self.webapp
		self.tracker = TrackerConnection()


class DataStore(object):
	def __init__(self, application):
		self.application = application
		self.db = Databases(self.application)

		self.reload()

	def reload(self):
		self.banners = banners.Banners(self.application, "banners.json")
		self.config = config.Config(self.application)
#		self.info = info.Info(self.application, "info.json")
		self.menu = menu.Menu(self.application, "menu.json")
#		self.mirrors = mirrors.Mirrors(self.application, "mirrors.json")
		self.news = news.News(self.application, "news.json")
		self.releases = releases.Releases(self.application, "releases.json")
		self.tracker = tracker.Tracker(self.application)

	def trigger(self):
		pass
