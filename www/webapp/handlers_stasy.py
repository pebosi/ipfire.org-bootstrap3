#!/usr/bin/python

import tornado.web

from handlers_base import *

class StasyBaseHandler(BaseHandler):
	@property
	def stasy(self):
		return backend.Stasy()


class StasyIndexHandler(StasyBaseHandler):
	def get(self):
		profiles = self.stasy.get_profiles()

		self.render("stasy-index.html", profiles=profiles)


class StasyProfileHandler(StasyBaseHandler):
	def get(self, profile_id):
		profile = self.stasy.get_profile(profile_id)
		if not profile:
			raise tornado.web.HTTPError(404, "Profile not found: %s" % profile_id)

		self.render("stasy-profile.html", profile=profile)
