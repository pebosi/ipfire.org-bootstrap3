#!/usr/bin/python

import datetime
import ipaddr
import logging
import pymongo
import re
import simplejson
import tornado.database
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

import webapp.backend as backend

# Enable logging
tornado.options.parse_command_line()

DATABASE_HOST = ["irma.ipfire.org", "madeye.ipfire.org"]
DATABASE_NAME = "stasy"

DEFAULT_HOST = "www.ipfire.org"

MIN_PROFILE_VERSION = 0
MAX_PROFILE_VERSION = 0

class Profile(dict):
	def __getattr__(self, key):
		try:
			return self[key]
		except KeyError:
			raise AttributeError, key

	def __setattr__(self, key, val):
		self[key] = val


class Stasy(tornado.web.Application):
	def __init__(self, **kwargs):
		settings = dict(
			debug = False,
			default_host = DEFAULT_HOST,
			gzip = True,
		)
		settings.update(kwargs)

		tornado.web.Application.__init__(self, **settings)

		# Establish database connection
		self.connection = pymongo.Connection(DATABASE_HOST)
		self.db = self.connection[DATABASE_NAME]
		logging.info("Successfully connected to database: %s:%s" % \
			(self.connection.host, self.connection.port))

		self.add_handlers(r"(fireinfo|stasy).ipfire.org", [
			(r"/", tornado.web.RedirectHandler, { "url" : "http://www.ipfire.org/" }),
			(r"/send/([a-z0-9]+)", ProfileSendHandler),
			(r"/debug", DebugHandler),
		])

		# ipfire.org
		#  this should not be neccessary (see default_host) but some versions
		#  of tornado have a bug.
		self.add_handlers(r".*", [
			(r".*", tornado.web.RedirectHandler, { "url" : "http://" + DEFAULT_HOST + "/" })
		])

	def __del__(self):
		logging.debug("Disconnecting from database")
		self.connection.disconnect()

	@property
	def ioloop(self):
		return tornado.ioloop.IOLoop.instance()

	def start(self, port=9001):
		logging.info("Starting application")

		http_server = tornado.httpserver.HTTPServer(self, xheaders=True)
		http_server.listen(port)

		# Register automatic cleanup for old profiles, etc.
		automatic_cleanup = tornado.ioloop.PeriodicCallback(
			self.automatic_cleanup, 60*60*1000)
		automatic_cleanup.start()

		self.ioloop.start()

	def stop(self):
		logging.info("Stopping application")
		self.ioloop.stop()

	def db_get_collection(self, name):
		return pymongo.collection.Collection(self.db, name)

	@property
	def profiles(self):
		return self.db_get_collection("profiles")

	@property
	def archives(self):
		return self.db_get_collection("archives")

	def automatic_cleanup(self):
		logging.info("Starting automatic cleanup...")

		# Remove all profiles that were not updated since 4 weeks.
		not_updated_since = datetime.datetime.utcnow() - \
			datetime.timedelta(weeks=4)

		self.move_profiles({ "updated" : { "$lt" : not_updated_since }})

	def move_profiles(self, find):
		"""
			Move all profiles by the "find" criteria.
		"""
		for p in self.profiles.find(find):
			self.archives.save(p)
		self.profiles.remove(find)


class BaseHandler(tornado.web.RequestHandler):
	@property
	def geoip(self):
		return backend.GeoIP()

	@property
	def db(self):
		return self.application.db

	def db_get_collection(self, name):
		return self.application.db_get_collection(name)

	@property
	def db_collections(self):
		return [self.db_get_collection(c) for c in self.db.collection_names()]


DEBUG_STR = """
Database information:
	Host: %(db_host)s:%(db_port)s

	All nodes: %(db_nodes)s

	%(collections)s

"""

DEBUG_COLLECTION_STR = """
	Collection: %(name)s
		Total documents: %(count)d
"""

class DebugHandler(BaseHandler):
	def get(self):
		# This handler is only available in debugging mode.
		if not self.application.settings["debug"]:
			return tornado.web.HTTPError(404)

		self.set_header("Content-type", "text/plain")

		conn, db = (self.application.connection, self.db)

		debug_info = dict(
			db_host = conn.host,
			db_port = conn.port,
			db_nodes = list(conn.nodes),
		)

		collections = []
		for collection in self.db_collections:
			collections.append(DEBUG_COLLECTION_STR % {
				"name" : collection.name, "count" : collection.count(),
			})
		debug_info["collections"] = "".join(collections)

		self.write(DEBUG_STR % debug_info)
		self.finish()


class ProfileSendHandler(BaseHandler):
	@property
	def archives(self):
		return self.application.archives

	@property
	def profiles(self):
		return self.application.profiles

	def prepare(self):
		# Create an empty profile.
		self.profile = Profile()

	def __check_attributes(self, profile):
		"""
			Check for attributes that must be provided,
		"""

		attributes = (
			"private_id",
			"profile_version",
			"public_id",
			"updated",
		)
		for attr in attributes:
			if not profile.has_key(attr):
				raise tornado.web.HTTPError(400, "Profile lacks '%s' attribute: %s" % (attr, profile))

	def __check_valid_ids(self, profile):
		"""
			Check if IDs contain valid data.
		"""

		for id in ("public_id", "private_id"):
			if re.match(r"^([a-f0-9]{40})$", "%s" % profile[id]) is None:
				raise tornado.web.HTTPError(400, "ID '%s' has wrong format: %s" % (id, profile))

	def __check_equal_ids(self, profile):
		"""
			Check if public_id and private_id are equal.
		"""

		if profile.public_id == profile.private_id:
			raise tornado.web.HTTPError(400, "Public and private IDs are equal: %s" % profile)

	def __check_matching_ids(self, profile):
		"""
			Check if a profile with the given public_id is already in the
			database. If so we need to check if the private_id matches.
		"""
		p = self.profiles.find_one({ "public_id" : profile["public_id"]})
		if not p:
			return

		p = Profile(p)
		if p.private_id != profile.private_id:
			raise tornado.web.HTTPError(400, "Mismatch of private_id: %s" % profile)

	def __check_profile_version(self, profile):
		"""
			Check if this version of the server software does support the
			received profile.
		"""
		version = profile.profile_version

		if version < MIN_PROFILE_VERSION or version > MAX_PROFILE_VERSION:
			raise tornado.web.HTTPError(400,
				"Profile version is not supported: %s" % version)

	def check_profile(self):
		"""
			This method checks if the blob is sane.
		"""

		checks = (
			self.__check_attributes,
			self.__check_valid_ids,
			self.__check_equal_ids,
			self.__check_profile_version,
			# These checks require at least one database query and should be done
			# at last.
			self.__check_matching_ids,
		)

		for check in checks:
			check(self.profile)

		# If we got here, everything is okay and we can go on...

	def move_profiles(self, find):
		self.application.move_profiles(find)

	# The GET method is only allowed in debugging mode.
	def get(self, public_id):
		if not self.application.settings["debug"]:
			return tornado.web.HTTPError(405)

		return self.post(public_id)

	def post(self, public_id):
		profile = self.get_argument("profile", None)

		# Send "400 bad request" if no profile was provided
		if not profile:
			raise tornado.web.HTTPError(400, "No profile received.")

		# Try to decode the profile.
		try:
			self.profile.update(simplejson.loads(profile))
		except simplejson.decoder.JSONDecodeError, e:
			raise tornado.web.HTTPError(400, "Profile could not be decoded: %s" % e)

		# Create a shortcut and overwrite public_id from query string
		profile = self.profile
		profile.public_id = public_id

		# Add timestamp to the profile
		profile.updated = datetime.datetime.utcnow()

		# Check if profile contains proper data.
		self.check_profile()

		# Get GeoIP information if address is not defined in rfc1918
		addr = ipaddr.IPAddress(self.request.remote_ip)
		if not addr.is_private:
			profile.geoip = self.geoip.get_all(self.request.remote_ip)

		# Move previous profiles to archive and keep only the latest one
		# in profiles. This will make full table lookups faster.
		self.move_profiles({ "public_id" : profile.public_id })

		# Write profile to database
		id = self.profiles.save(profile)

		self.write("Your profile was successfully saved to the database.")
		self.finish()

		logging.debug("Saved profile: %s" % profile)


if __name__ == "__main__":
	app = Stasy()

	app.start()
