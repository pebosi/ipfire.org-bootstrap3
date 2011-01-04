#!/usr/bin/python

from __future__ import division

import hwdata
import tornado.web

import backend

from handlers_base import *

class StasyBaseHandler(BaseHandler):
	@property
	def stasy(self):
		return backend.Stasy()

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


class StasyIndexHandler(StasyBaseHandler):
	def get(self):
		self.render("stasy-index.html")

	def post(self):
		profile_id = self.get_argument("profile_id", None)
		if not profile_id:
			raise tornado.web.HTTPError(400, "No profile ID was given.")

		if not self.stasy.profile_exists(profile_id):
			raise tornado.web.HTTPError(404, "Profile does not exist.")

		self.redirect("/profile/%s" % profile_id)


class StasyProfileDetailHandler(StasyBaseHandler):
	def get(self, profile_id):
		profile = self.stasy.get_profile(profile_id)
		if not profile:
			raise tornado.web.HTTPError(404, "Profile not found: %s" % profile_id)

		self.render("stasy-profile-detail.html", profile=profile)


class StasyStatsHandler(StasyBaseHandler):
	def get(self):
		self.render("stasy-stats.html")


class StasyStatsCPUHandler(StasyBaseHandler):
	def get(self):
		return self.render("stasy-stats-cpus.html",
			cpu_vendors=self.stasy.cpu_vendors_map,
			average_speed=self.stasy.cpu_speed_average,
			cpu_speeds=self.stasy.cpu_speed_map)


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

		print kwargs

		return self.render("stasy-stats-cpu-flags.html", **kwargs)

class StasyStatsMemoryHandler(StasyBaseHandler):
	def get(self):
		return self.render("stasy-stats-memory.html",
			average_memory=self.stasy.memory_average,
			memory=self.stasy.get_memory_map())


class StasyStatsOSesHandler(StasyBaseHandler):
	def get(self):
		return self.render("stasy-stats-oses.html",
			arches=self.stasy.arch_map,
			kernels=self.stasy.kernel_map,
			releases=self.stasy.release_map)


class StasyStatsVirtualHandler(StasyBaseHandler):
	def get(self):
		return self.render("stasy-stats-virtual.html",
			hypervisor_vendors = self.stasy.hypervisor_map,
			is_virtual = self.stasy.virtual_map)

class StasyStatsGeoHandler(StasyBaseHandler):
	def get(self):
		return self.render("stasy-stats-geo.html",
			languages = self.stasy.get_language_map(),
			geo_locations = self.stasy.get_geo_location_map())


class StasyStatsNetworkHandler(StasyBaseHandler):
	def get(self):
		return self.render("stasy-stats-network.html",
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

		self.render("stasy-vendor-detail.html",
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

		self.render("stasy-model-detail.html",
			vendor_id=vendor_id,
			vendor_name=vendor_name,
			model_id=model_id,
			model_name=model_name,
			percentage=percentage)
