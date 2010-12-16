#!/usr/bin/python

import hwdata
import logging
import pymongo

from misc import Singleton

DATABASE_HOST = ["irma.ipfire.org", "madeye.ipfire.org"]
DATABASE_NAME = "stasy"

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
	def model(self):
		return self._data.get("model")

	@property
	def model_string(self):
		return self._data.get("model_string")

	@property
	def flags(self):
		return self._data.get("flags")

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
	def model(self):
		return self._data.get("model")

	@property
	def type(self):
		return self._data.get("type")


class ProfileDevice(ProfileDict):
	subsystem2class = {
		"pci" : hwdata.PCI,
		"usb" : hwdata.USB,
	}

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


class Profile(ProfileDict):
	def __init__(self, public_id, updated, data):
		ProfileDict.__init__(self, data)

		self.public_id = public_id
		self.updated = updated

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

			if d.driver in ("usb", "hub"):
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
		return self.system.get("root_size")



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

	def get_profile(self, public_id):
		# XXX should only find one object in the end
		for p in self._db.profiles.find({ "public_id" : public_id }):
			p = Profile(p.get("public_id"), p.get("updated"), p.get("profile"))

		return p

	def get_profiles(self):
		# XXX needs nicer database query
		profiles = []
		for p in self._db.profiles.find():
			if not p.get("public_id") in profiles:
				profiles.append(p.get("public_id"))

		return profiles

	@property
	def secret_ids(self):
		return self._db.profiles.distinct("secret_id")

	@property
	def cpus(self):
		return self._db.profiles.distinct("profile.cpu")

	@property
	def cpu_vendors(self):
		return self._db.profiles.distinct("profile.cpu.vendor")

	@property
	def cpu_map(self):
		cpus = {}

		for vendor in self.cpu_vendors:
			cpus[vendor] = \
				self._db.profiles.find({
					"profile.cpu.vendor" : vendor
				}).count()

		return cpus

	@property
	def memory_map(self):
		memory = {}

		for i in range(len(MEMORY_CONSTRAINTS) - 1):
			min, max = MEMORY_CONSTRAINTS[i:i+2]

			memory[min, max] = \
				self._db.profiles.find(
					{ "profile.system.memory" : {
						"$gte" : min * 1024, "$lt" : max * 1024
					}
				}).count()

		return memory

	@property
	def memory_average(self):
		memory = 0

		all = self._db.profiles.find()

		# XXX ugly. needs to be done by group()
		for m in all:
			if not m.has_key("profile"):
				continue
			memory += int(m.get("profile").get("system").get("memory"))

		return (memory / all.count()) / 1024

	@property
	def hypervisor_vendors(self):
		return self._db.profiles.distinct("profile.hypervisor.vendor")

	@property
	def hypervisor_map(self):
		hypervisors = {}

		for hypervisor in self.hypervisor_vendors:
			hypervisors[hypervisor] = \
				self._db.profiles.find({
					"profile.hypervisor.vendor" : hypervisor
				}).count()

		return hypervisors

	@property
	def hypervisor_models(self):
		return self._db.profiles.distinct("profile.hypervisor.model")

	@property
	def virtual_map(self):
		virtual = {
			True: None,
			False: None,
		}

		for k in virtual.keys():
			virtual[k] = \
				self._db.profiles.find({ "profile.system.virtual": k }).count()

		return virtual

	@property
	def languages(self):
		return self._db.profiles.distinct("profile.system.language")

	@property
	def vendors(self):
		return self._db.profiles.distinct("profile.system.vendor")

	@property
	def vendor_map(self):
		vendors = {}

		for vendor in self.vendors:
			vendors[vendor] = \
				self._db.profiles.find({
					"profile.system.vendor" : vendor
				}).count()

		return vendors

	@property
	def models(self):
		return self._db.profiles.distinct("profile.system.model")



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
	print s.vendors
	print s.vendor_map
	print s.models
	print s.cpus

	p = s.get_profile("0b5f4fe2162fdfbfa29b632610e317078fa70d34")
	print p
	print p.hypervisor
