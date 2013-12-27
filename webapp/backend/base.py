#!/usr/bin/python

import ConfigParser as configparser

import accounts
import ads
import database
import geoip
import iuse
import memcached
import mirrors
import netboot
import news
import planet
import releases
import settings
import stasy
import tracker
import wishlist

class Backend(object):
	def __init__(self, configfile):
		# Read configuration file.
		self.config = self.read_config(configfile)

		# Setup database.
		self.setup_database()

		# Initialize settings first.
		self.settings = settings.Settings(self)
		self.memcache = memcached.Memcached(self)

		# Initialize backend modules.
		self.accounts = accounts.Accounts(self)
		self.advertisements = ads.Advertisements(self)
		self.downloads = mirrors.Downloads(self)
		self.geoip = geoip.GeoIP(self)
		self.iuse = iuse.IUse(self)
		self.mirrors = mirrors.Mirrors(self)
		self.netboot = netboot.NetBoot(self)
		self.news = news.News(self)
		self.planet = planet.Planet(self)
		self.releases = releases.Releases(self)
		self.stasy = stasy.Stasy(self)
		self.tracker = tracker.Tracker(self)
		self.wishlist = wishlist.Wishlist(self)

	def read_config(self, configfile):
		cp = configparser.ConfigParser()
		cp.read(configfile)

		return cp

	def setup_database(self):
		"""
			Sets up the database connection.
		"""
		credentials = {
			"host"     : self.config.get("database", "server"),
			"database" : self.config.get("database", "database"),
			"user"     : self.config.get("database", "username"),
			"password" : self.config.get("database", "password"),
		}

		self.db = database.Connection(**credentials)
