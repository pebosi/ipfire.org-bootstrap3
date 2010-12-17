#!/usr/bin/python

from __future__ import division

import StringIO

from PIL import Image, ImageDraw, PngImagePlugin

from misc import Singleton

class IUse(object):
	__metaclass__ = Singleton

	images = []

	def add_imagetype(self, type):
		self.images.append(type)

	def get_imagetype(self, id):
		id = int(id)

		for image in self.images:
			if image.id == id:
				return image


class ImageObject(object):
	default_mode = "RGBA"
	default_size = 100, 100

	def __init__(self, profile):
		self.profile = profile

		# Create new image
		self._image = Image.new(self.default_mode, self.default_size)

		self.draw()

	def open(self, filename):
		image = Image.open(filename, self.default_mode)
		self._image = image.convert(self.default_mode)

	def save(self, filename):
		self._image.save(filename, "PNG", optimize=True)

	def to_string(self):
		f = StringIO.StringIO()

		self.save(f)

		return f.getvalue()

	@property
	def paint(self):
		if not hasattr(self, "_draw"):
			self._draw = ImageDraw.Draw(self._image)

		return self._draw

	def draw(self):
		raise NotImplementedError


class Image1(ImageObject):
	id = 0

	default_size = 500, 50

	def draw(self):
		# Background
		self.paint.rectangle(((0, 0), self.default_size), fill="#000000")

		# Release information
		self.paint.text((10, 10), "%s" % self.profile.release)

		# Hardware information
		hw = [
			self.profile.cpu.model_string,
			"Memory: %.1fG" % (self.profile.memory / 1024**2),
		]

		if self.profile.virtual:
			virt = "V-%s" % self.profile.hypervisor.vendor
			if self.profile.hypervisor.type == "PV":
				virt = "%s-PV" % virt
			hw.append(virt)

		if self.profile.cpu.capable_64bit:
			hw.append("64")

		self.paint.text((10, 30), "%s" % " | ".join(hw))


IUse().add_imagetype(Image1)


if __name__ == "__main__":
	image = Image1("123")
	image.save("picture.png")

