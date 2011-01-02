#!/usr/bin/python

from __future__ import division

import hwdata
import logging
import pymongo

from misc import Singleton

DATABASE_HOST = ["irma.ipfire.org", "madeye.ipfire.org"]
DATABASE_NAME = "stasy"

CPU_SPEED_CONSTRAINTS = (0, 500, 1000, 1500, 2000, 2500, 3000, 3500)
MEMORY_CONSTRAINTS = (0, 64, 128, 256, 512, 1024, 2048, 4096, 8128, 16384)

class ProfileDict(object):
	def __init__(self, data):
		self._data = data


class ProfileCPU(ProfileDict):
	@property
	def arch(self):
		return self._data.get("arch")

	@property
	def vendor(self):
		return self._data.get("vendor")

	@property
	def speed(self):
		return self._data.get("speed")

	@property
	def bogomips(self):
		return self._data.get("bogomips")

	@property
	def model(self):
		return self._data.get("model")

	@property
	def model_string(self):
		return self._data.get("model_string")

	@property
	def flags(self):
		return self._data.get("flags")

	@property
	def count(self):
		return self._data.get("count")

	@property
	def capable_64bit(self):
		return "lm" in self.flags

	@property
	def capable_pae(self):
		return "pae" in self.flags

	@property
	def capable_virt(self):
		return "vmx" in self.flags or "svm" in self.flags


class ProfileHypervisor(ProfileDict):
	def __repr__(self):
		return "<%s %s-%s>" % (self.__class__.__name__, self.vendor, self.type)

	@property
	def vendor(self):
		return self._data.get("vendor")

	@property
	def type(self):
		return self._data.get("type")


class ProfileNetwork(ProfileDict):
	def has_zone(self, name):
		return self._data.get(name)

	@property
	def green(self):
		return self._data.get("green")

	@property
	def red(self):
		return self._data.get("red")

	@property
	def blue(self):
		return self._data.get("blue")

	@property
	def orange(self):
		return self._data.get("orange")


class ProfileDevice(ProfileDict):
	subsystem2class = {
		"pci" : hwdata.PCI,
		"usb" : hwdata.USB,
	}

	classid2name = {
		"pci" : {
			"00" : "Unclassified",
			"01" : "Mass storage",
			"02" : "Network",
			"03" : "Display",
			"04" : "Multimedia",
			"05" : "Memory controller",
			"06" : "Bridge",
			"07" : "Communication",
			"08" : "Generic system peripheral",
			"09" : "Input device",
			"0a" : "Docking station",
			"0b" : "Processor",
			"0c" : "Serial bus",
			"0d" : "Wireless",
			"0e" : "Intelligent controller",
			"0f" : "Satellite communications controller",
			"10" : "Encryption",
			"11" : "Signal processing controller",
			"ff" : "Unassigned class",
		},
		
		"usb" : {
			"00" : "Unclassified",
			"01" : "Multimedia",
			"02" : "Communication",
			"03" : "Input device",
			"05" : "Generic system peripheral",
			"06" : "Image",
			"07" : "Printer",
			"08" : "Mass storage",
			"09" : "Hub",
			"0a" : "Communication",
			"0b" : "Smart card",
			"0d" : "Encryption",
			"0e" : "Display",
			"0f" : "Personal Healthcare",
			"dc" : "Diagnostic Device",
			"e0" : "Wireless",
			"ef" : "Unclassified",
			"fe" : "Unclassified",
			"ff" : "Unclassified",
		}
	}

	def __cmp__(self, other):
		return cmp(self.vendor, other.vendor) or \
			cmp(self.model, other.model) or \
			cmp(self.driver, other.driver)

	@property
	def model(self):
		return self._data.get("model")

	@property
	def model_string(self):
		cls = self.subsystem2class[self.subsystem]

		return cls().get_device(self.vendor, self.model)

	@property
	def subsystem(self):
		return self._data.get("subsystem")

	@property
	def vendor(self):
		return self._data.get("vendor")

	@property
	def vendor_string(self):
		cls = self.subsystem2class[self.subsystem]

		return cls().get_vendor(self.vendor)

	@property
	def driver(self):
		return self._data.get("driver")

	@property
	def cls(self):
		classid = self._data.get("deviceclass")

		if self.subsystem == "pci":
			classid = classid[:-4]
			if len(classid) == 1:
				classid = "0%s" % classid

		elif self.subsystem == "usb" and classid:
			classid = classid.split("/")[0]
			classid = "%02x" % int(classid)

		try:
			return self.classid2name[self.subsystem][classid]
		except KeyError:
			return "N/A"


class Profile(ProfileDict):
	def __init__(self, profile_blob):
		ProfileDict.__init__(self, profile_blob.get("profile"))

		self.public_id = profile_blob.get("public_id")
		self.updated = profile_blob.get("updated")
		self._geoip = profile_blob.get("geoip", None)

	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.public_id)

	@property
	def cpu(self):
		return ProfileCPU(self._data.get("cpu"))

	@property
	def devices(self):
		devices = []
		for d in self._data.get("devices"):
			d = ProfileDevice(d)

			if d.driver in ("pcieport", "usb", "hub"):
				continue

			devices.append(d)

		return devices

	@property
	def hypervisor(self):
		if self.virtual:
			return ProfileHypervisor(self._data.get("hypervisor"))

	@property
	def virtual(self):
		return self.system.get("virtual")

	@property
	def system(self):
		return self._data.get("system")

	@property
	def release(self):
		return self.system.get("release")

	@property
	def kernel(self):
		return self.system.get("kernel_release")

	@property
	def memory(self):
		return self.system.get("memory")

	@property
	def root_size(self):
		return self.system.get("root_size") or 0

	@property
	def vendor(self):
		return self.system.get("vendor")

	@property
	def model(self):
		return self.system.get("model")

	@property
	def country_code(self):
		if self._geoip:
			return self._geoip["country_code"].lower()

		return "unknown"

	@property
	def network(self):
		network = self._data.get("network", None)
		if network:
			return ProfileNetwork(network)


class Stasy(object):
	__metaclass__ = Singleton

	def __init__(self):
		# Initialize database connection
		self._conn = pymongo.Connection(DATABASE_HOST)
		self._db = self._conn[DATABASE_NAME]

	def get_profile_count(self):
		# XXX need to implement something to get profiles updated since
		# a given date

		# All distinct profiles (based on public_id)
		return self._db.profiles.distinct("public_id").count()

	#def _get_profile_cursor(self, public_id):
	#	c = self._db.profiles.find({ "public_id" : public_id })
	#	c.sort("updated", pymongo.ASCENDING)
	#
	#	return c

	def profile_exists(self, public_id):
		return self.query({ "public_id" : public_id }).count() >= 1

	def get_profile(self, public_id):
		p = None
		# XXX should only find one object in the end
		for p in self.query({ "public_id" : public_id }):
			p = Profile(p)

		return p

	def get_profiles(self):
		# XXX needs nicer database query
		profiles = []
		for p in self._db.profiles.find():
			if not p.get("public_id") in profiles:
				profiles.append(p.get("public_id"))

		return profiles

	def query(self, query, archives=False, no_virt=False, all=False):
		db = self._db.profiles

		if archives:
			db = self.db.archives

		if not all:
			# XXX cannot use the index?
			query.update({ "profile" : { "$exists" : True }})

		if no_virt:
			query.update({ "profile.system.virtual" : False })

		logging.debug("Executing query: %s" % query)

		return db.find(query)

	@property
	def secret_ids(self):
		return self._db.profiles.distinct("secret_id")

	@property
	def cpus(self):
		return self.query({}, no_virt=True).distinct("profile.cpu")

	@property
	def cpu_vendors(self):
		return self.query({}, no_virt=True).distinct("profile.cpu.vendor")

	@property
	def cpu_vendors_map(self):
		cpus = {}

		for vendor in self.cpu_vendors:
			cpus[vendor] = \
				self.query({
					"profile.cpu.vendor" : vendor
				}, no_virt=True).count()

		return cpus

	@property
	def cpu_speed_average(self):
		speed = 0

		all = self.query({}, no_virt=True)

		# XXX ugly. needs to be done by group()
		for m in all:
			if not m.has_key("profile"):
				continue
			speed += m.get("profile").get("cpu").get("speed")

		return (speed / all.count())

	@property
	def cpu_speed_map(self):
		cpu_speeds = {}

		for i in range(len(CPU_SPEED_CONSTRAINTS) - 1):
			min, max = CPU_SPEED_CONSTRAINTS[i:i+2]

			cpu_speeds[min, max] = \
				self.query({
					"profile.cpu.speed" : {
						"$gte" : min, "$lt" : max
					}
				}, no_virt=True).count()

		return cpu_speeds

	def get_memory_map(self):
		memory = {}

		for i in range(len(MEMORY_CONSTRAINTS) - 1):
			min, max = MEMORY_CONSTRAINTS[i:i+2]

			memory[min, max] = \
				self.query(
					{ "profile.system.memory" : {
						"$gte" : min * 1024, "$lt" : max * 1024
					}
				}, no_virt=True).count()

		return memory

	@property
	def memory_average(self):
		memory = 0

		all = self.query({}, no_virt=True)

		# XXX ugly. needs to be done by group()
		for m in all:
			if not m.has_key("profile"):
				continue
			memory += int(m.get("profile").get("system").get("memory"))

		return (memory / all.count()) / 1024

	@property
	def hypervisor_vendors(self):
		return self.query({}).distinct("profile.hypervisor.vendor")

	@property
	def hypervisor_map(self):
		hypervisors = {}

		for hypervisor in self.hypervisor_vendors:
			hypervisors[hypervisor] = \
				self.query({
					"profile.hypervisor.vendor" : hypervisor
				}).count()

		return hypervisors

	@property
	def hypervisor_models(self):
		return self.query({}).distinct("profile.hypervisor.model")

	@property
	def virtual_map(self):
		virtual = {
			True: None,
			False: None,
		}

		for k in virtual.keys():
			virtual[k] = \
				self.query({ "profile.system.virtual": k }).count()

		return virtual

	@property
	def languages(self):
		return self.query({}).distinct("profile.system.language")

	def get_language_map(self):
		languages = {}

		for language in self.languages:
			languages[language] = \
				self.query({
					"profile.system.language" : language
				}).count()

		return languages

	@property
	def vendors(self):
		return self.query({}).distinct("profile.system.vendor")

	@property
	def vendor_map(self):
		vendors = {}

		for vendor in self.vendors:
			vendors[vendor] = \
				self.query({
					"profile.system.vendor" : vendor
				}).count()

		return vendors

	@property
	def models(self):
		return self.query({}).distinct("profile.system.model")

	@property
	def model_map(self):
		models = {}

		for model in self.models:
			models[model] = \
				self.query({
					"profile.system.model" : model
				}).count()

		return models

	@property
	def arches(self):
		return self.query({}).distinct("profile.cpu.arch")

	@property
	def arch_map(self):
		arches = {}

		for arch in self.arches:
			arches[arch] = \
				self.query({
					"profile.cpu.arch" : arch
				}).count()

		return arches

	@property
	def kernels(self):
		return self.query({}).distinct("profile.system.kernel_release")

	@property
	def kernel_map(self):
		kernels = {}

		for kernel in self.kernels:
			kernels[kernel] = \
				self.query({
					"profile.system.kernel_release" : kernel
				}).count()

		return kernels

	@property
	def releases(self):
		return self.query({}).distinct("profile.system.release")

	@property
	def release_map(self):
		releases = {}

		for release in self.releases:
			releases[release] = \
				self.query({
					"profile.system.release" : release
				}).count()

		return releases

	def get_device_percentage(self, bus, vendor_id, model_id):
		profiles_with_device = self.query({
			"profile.devices.subsystem" : bus,
			"profile.devices.vendor" : vendor_id,
			"profile.devices.model" : model_id,
		})

		profiles_all = self.query({})

		if not profiles_all.count():
			return 0

		return profiles_with_device.count() / profiles_all.count()

	def get_cpu_flag_map(self, flags):
		# XXX needs a cleanup

		_flags = { True : 0 }

		if type(flags) == type("a"):
			flags = [flags]

		for flag in flags:
			_flags[True] += \
				self.query({
					"profile.cpu.flags" : flag,
				}, no_virt=True).count()

		_flags[False] = self.query({}, no_virt=True).count() - _flags[True]

		return _flags

	@property
	def geo_locations(self):
		return [code.lower() for code in self.query({}).distinct("geoip.country_code")]

	def get_geo_location_map(self):
		geo_locations = {}

		count = 0
		for geo_location in self.geo_locations:
			geo_locations[geo_location] = \
				self.query({
					"geoip.country_code" : geo_location
				}).count()

			count += geo_locations[geo_location]

		# XXX must only be systems that have profile data
		profiles_all = self.query({})

		unknown_count = profiles_all.count() - count
		if unknown_count:
			geo_locations["unknown"] = unknown_count

		return geo_locations

	def get_models_by_vendor(self, subsystem, vendor_id):
		devices = []

		# XXX must only be systems that have profile data
		profiles_all = self.query({})

		for profile in profiles_all:
			if not profile.has_key("profile"):
				continue

			profile = Profile(profile)

			for device in profile.devices:
				if not device.vendor == vendor_id:
					continue

				if not device in devices:
					devices.append(device)

		return devices

	def get_network_zones_map(self):
		zones = { "green" : 0, "blue" : 0, "orange" : 0, "red" : 0 }

		for zone in zones.keys():
			zones[zone] = self.query({
				"profile.network.%s" % zone : True,
			}).count()

		return zones


if __name__ == "__main__":
	s = Stasy()

	print s.get_profile("0" * 40)
	print s.cpu_vendors
	for id in s.secret_ids:
		print "\t", id

	#for p in s._db.profiles.find():
	#	print p

	print s.cpu_map
	print s.memory_map
	print s.memory_average
	print s.hypervisor_vendors
	print s.hypervisor_models
	print s.languages
	print s.language_maps
	print s.vendors
	print s.vendor_map
	print s.models
	print s.cpus
	print s.cpu_map
	print s.arches
	print s.arch_map
	print s.kernels
	print s.kernel_map
	print s.releases
	print s.release_map

	p = s.get_profile("0b5f4fe2162fdfbfa29b632610e317078fa70d34")
	print p._data
#	print p.hypervisor

