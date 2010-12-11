#!/usr/bin/python

import logging
import pymongo

DATABASE_HOST = ["irma.ipfire.org", "madeye.ipfire.org"]
DATABASE_NAME = "stasy"

class ProfileDict(object):
	def __init__(self, data):
		self._data = data

		logging.debug("New: %s" % self._data)

	def __repr__(self):
		return self.__str__()

	def __str__(self):
		return "<%s %s>" % (self.__class__.__name__, self.public_id)

	def __getattr__(self, key):
		try:
			return self._data[key]
		except KeyError:
			raise AttributeError, key

	def __setattr(self, key, val):
		self._data[key] = val


class ProfileCPU(ProfileDict):
	@property
	def capable_64bit(self):
		return "lm" in self.flags

	@property
	def capable_pae(self):
		return "pae" in self.flags


class ProfileHypervisor(ProfileDict):
	pass


class ProfileDevice(ProfileDict):
	@property
	def model_string(self):
		return "XXX"

	@property
	def vendor_string(self):
		return "XXX"


class Profile(ProfileDict):
	def __repr__(self):
		return "<%s %s>" % (self.__class__.__name__, self.public_id)

	@property
	def cpu(self):
		return ProfileCPU(self._data["cpu"])

	@property
	def hypervisor(self):
		return ProfileHypervisor(self._data["hypervisor"])

	@property
	def devices(self):
		return [ProfileDevice(d) for d in self._data["devices"]]


class StasyDatabase(object):
	def __init__(self):
		# Initialize database connection
		self._conn = pymongo.Connection(DATABASE_HOST)
		self._db = self._conn[DATABASE_NAME]

	def get_profile_count(self):
		# XXX need to implement something to get profiles updated since
		# a given date

		# All distinct profiles (based on public_id)
		c = self._db.profiles.find().distinct("public_id")

		return c.count()

	def _get_profile_cursor(self, public_id):
		c = self._db.profiles.find({ "public_id" : public_id })
		c.sort("updated", pymongo.ASCENDING)

		return c

	def get_latest_profile(self, public_id):
		# XXX still finds first one
		for p in self._get_profile_cursor(public_id).limit(1):
			return Profile(p)

	def get_profiles(self):
		# XXX needs nicer database query
		profiles = []
		for p in self._db.profiles.find():
			p = Profile(p)
			if not p.public_id in profiles:
				profiles.append(p.public_id)

		return profiles

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
				self._db.profiles.find({ "profile.cpu.vendor" : vendor }).count()

		return cpus

	@property
	def hypervisor_vendors(self):
		return self._db.profiles.distinct("profile.hypervisor.vendor")

	@property
	def hypervisor_models(self):
		return self._db.profiles.distinct("profile.hypervisor.model")

	@property
	def secret_ids(self):
		return self._db.profiles.distinct("secret_id")

	@property
	def languages(self):
		return self._db.profiles.distinct("profile.system.language")

	@property
	def vendors(self):
		return self._db.profiles.distinct("profile.system.vendor")

	@property
	def models(self):
		return self._db.profiles.distinct("profile.system.model")


class Stasy(object):
	def __init__(self):
		self.db = StasyDatabase()

	def get_profile(self, public_id):
		return self.db.get_latest_profile(public_id)

	def get_profiles(self):
		return self.db.get_profiles()


if __name__ == "__main__":
	s = Stasy()

	print s.get_profile("0" * 40)
	print s.db.cpu_vendors
	for id in s.db.secret_ids:
		print "\t", id

	for p in s.db._db.profiles.find():
		print p

	print s.db.cpu_map
	print s.db.hypervisor_vendors
	print s.db.hypervisor_models
	print s.db.languages
	print s.db.vendors
	print s.db.models
	print s.db.cpus
