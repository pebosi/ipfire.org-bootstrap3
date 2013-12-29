#!/usr/bin/python

from __future__ import division

import datetime
import hwdata
import ipaddr
import logging
import re
import simplejson
import tornado.web

import backend

from handlers_base import *

class StasyBaseHandler(BaseHandler):
	def format_size(self, s):
		units = ("K", "M", "G", "T")
		unit = 0

		while s >= 1024 and unit < len(units):
			s /= 1024
			unit += 1

		return "%.1f%s" % (s, units[unit])

	def cut_string(self, s, limit=15):
		if len(s) > limit:
			s = s[:limit] + "..."

		return s

	def render(self, *args, **kwargs):
		kwargs.update({
			"cut_string" : self.cut_string,
			"format_size" : self.format_size,
		})

		return BaseHandler.render(self, *args, **kwargs)


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


class StasyProfileSendHandler(StasyBaseHandler):
	def check_xsrf_cookie(self):
		# This cookie is not required here.
		pass

	@property
	def archives(self):
		return self.stasy.archives

	@property
	def profiles(self):
		return self.stasy.profiles

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
		remote_ips = self.request.remote_ip.split(", ")
		for remote_ip in remote_ips:
			try:
				addr = ipaddr.IPAddress(remote_ip)
			except ValueError:
				# Skip invalid IP addresses.
				continue

			# Check if the given IP address is from a
			# private network.
			if addr.is_private:
				continue

			location = self.geoip.get_location(remote_ip)
			if location:
				profile.geoip = {
					"country_code" : location.country,
				}
			else:
				profile.geoip = None

			break

		# Move previous profiles to archive and keep only the latest one
		# in profiles. This will make full table lookups faster.
		self.stasy.move_profiles({ "public_id" : profile.public_id })

		# Write profile to database
		id = self.profiles.save(profile)

		self.write("Your profile was successfully saved to the database.")
		self.finish()

		logging.debug("Saved profile: %s" % profile)

	def on_finish(self):
		logging.debug("Starting automatic cleanup...")

		# Remove all profiles that were not updated since 4 weeks.
		not_updated_since = datetime.datetime.utcnow() - \
			datetime.timedelta(weeks=4)

		self.stasy.move_profiles({ "updated" : { "$lt" : not_updated_since }})


class StasyIndexHandler(StasyBaseHandler):
	def _profile_not_found(self, profile_id):
		self.set_status(404)
		self.render("fireinfo/profile-notfound.html", profile_id=profile_id)

	def get(self):
		self.render("fireinfo/index.html")

	def post(self):
		profile_id = self.get_argument("profile_id", None)
		if not profile_id:
			raise tornado.web.HTTPError(400, "No profile ID was given.")

		if not self.stasy.profile_exists(profile_id):
			self._profile_not_found(profile_id)
			return

		self.redirect("/profile/%s" % profile_id)


class StasyProfileDetailHandler(StasyIndexHandler):
	def get(self, profile_id):
		profile = self.stasy.get_profile(profile_id)
		if not profile:
			self._profile_not_found(profile_id)
			return

		self.render("fireinfo/profile-detail.html", profile=profile)


class StasyStatsHandler(StasyBaseHandler):
	def get(self):
		self.render("fireinfo/stats.html")


class StasyStatsCPUHandler(StasyBaseHandler):
	def get(self):
		return self.render("fireinfo/stats-cpus.html",
			cpu_vendors=self.stasy.cpu_vendors_map,
			average_speed=self.stasy.cpu_speed_average,
			cpu_speeds=self.stasy.cpu_speed_map,
			cpu_cores=self.stasy.get_cpu_cores_map(),
			bogomips=self.stasy.get_cpu_bogomips_accumulated())


class StasyStatsCPUFlagsHandler(StasyBaseHandler):
	def get(self):
		kwargs = {}
		
		flags = (
			("lm", "lm"),
			("pae", "pae"),
			("virt", ("vmx", "svm")),
		)

		for name, flag in flags:
			kwargs["cpus_" + name] = self.stasy.get_cpu_flag_map(flag)

		return self.render("fireinfo/stats-cpu-flags.html", **kwargs)

class StasyStatsMemoryHandler(StasyBaseHandler):
	def get(self):
		return self.render("fireinfo/stats-memory.html",
			average_memory=self.stasy.memory_average,
			memory=self.stasy.get_memory_map())


class StasyStatsOSesHandler(StasyBaseHandler):
	def get(self):
		return self.render("fireinfo/stats-oses.html",
			arches=self.stasy.arch_map,
			kernels=self.stasy.kernel_map,
			releases=self.stasy.release_map)


class StasyStatsVirtualHandler(StasyBaseHandler):
	def get(self):
		return self.render("fireinfo/stats-virtual.html",
			hypervisor_vendors = self.stasy.hypervisor_map,
			is_virtual = self.stasy.virtual_map)

class StasyStatsGeoHandler(StasyBaseHandler):
	def get(self):
		return self.render("fireinfo/stats-geo.html",
			languages = self.stasy.get_language_map(),
			geo_locations = self.stasy.get_geo_location_map())


class StasyStatsNetworkHandler(StasyBaseHandler):
	def get(self):
		return self.render("fireinfo/stats-network.html",
			network_zones=self.stasy.get_network_zones_map())


class StasyStatsVendorDetail(StasyBaseHandler):
	def get(self, bus, vendor_id):
		# XXX some way ugly
		bus2cls = {
			"pci" : hwdata.PCI,
			"usb" : hwdata.USB
		}
		cls = bus2cls[bus.lower()]
		vendor_name = cls().get_vendor(vendor_id)

		# Get a list of all models we know from this vendor
		models = self.stasy.get_models_by_vendor(bus, vendor_id)

		self.render("fireinfo/vendor-detail.html",
			vendor_name=vendor_name, models=models)


class StasyStatsModelDetail(StasyBaseHandler):
	def get(self, bus, vendor_id, model_id):
		bus2cls = {
			"pci" : hwdata.PCI,
			"usb" : hwdata.USB
		}
		
		cls = bus2cls[bus.lower()]

		vendor_name = cls().get_vendor(vendor_id)
		model_name = cls().get_device(vendor_id, model_id)
		
		percentage = \
			self.stasy.get_device_percentage(bus, vendor_id, model_id) * 100

		self.render("fireinfo/model-detail.html",
			vendor_id=vendor_id,
			vendor_name=vendor_name,
			model_id=model_id,
			model_name=model_name,
			percentage=percentage,
			bus=bus.lower())


class AdminFireinfoStatsHandler(StasyBaseHandler):
	def get(self):
		_ = self.locale.translate

		data = {}

		data["profiles_count"], data["profiles_count_all"] = \
			self.stasy.get_profile_ratio()

		data["archives_count"] = self.stasy.get_archives_count()

		# updated since 24h
		#since = { "hours" : 24 }
		#updates = self.stasy.get_updates_by_release_since(since)
		#updates[_("All versions")] = self.stasy.get_updated_since(since).count()
		#data["updated_since_24h"] = updates

		self.render("fireinfo/stats-admin.html", **data)

