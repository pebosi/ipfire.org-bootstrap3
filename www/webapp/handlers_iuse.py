#!/usr/bin/python

import tornado.web

from handlers_base import *
import backend

class IUseImage(BaseHandler):
	@property
	def iuse(self):
		return backend.IUse()

	@property
	def stasy(self):
		return backend.Stasy()

	def get(self, profile_id, image_id):
		image_cls = self.iuse.get_imagetype(image_id)
		if not image_cls:
			raise tornado.web.HTTPError(404, "Image class is unknown: %s" % image_id)

		profile = self.stasy.get_profile(profile_id)
		if not profile:
			raise tornado.web.HTTPError(404, "Profile '%s' was not found." % profile_id)

		self.set_header("Content-type", "image/png")

		# Render the image
		# XXX use memcached at this place
		image = image_cls(profile)

		self.write(image.to_string())

