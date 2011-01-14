#!/usr/bin/python

import logging
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
		image = None
		# Try to get the image from memcache. If we have a cache miss we
		# build a new one.
		mem_id = "iuse-%s-%s-%s" % (profile_id, image_id, self.locale.code)

		cache = self.get_argument("cache", "true")
		if cache == "true":
			image = self.memcached.get(mem_id)

		if image:
			logging.debug("Got image from cache for profile: %s" % profile_id)
		else:
			logging.info("Rendering new image for profile: %s" % profile_id)

			image_cls = self.iuse.get_imagetype(image_id)
			if not image_cls:
				raise tornado.web.HTTPError(404, "Image class is unknown: %s" % image_id)

			profile = self.stasy.get_profile(profile_id)
			if not profile:
				raise tornado.web.HTTPError(404, "Profile '%s' was not found." % profile_id)

			# Render the image
			image = image_cls(self, profile).to_string()

			# Save the image to the memcache for 15 minutes
			self.memcached.set(mem_id, image, 15*60)

		self.set_header("Content-Type", "image/png")
		self.write(image)

