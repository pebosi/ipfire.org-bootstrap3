#!/usr/bin/python

from __future__ import division

import StringIO
import logging
import os.path

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

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

	_filename = None
	_font = "DejaVuSans.ttf"
	_font_size = 10

	def __init__(self, request, profile):
		self.request = request
		self.profile = profile

		# Create new image
		if self.filename and os.path.exists(self.filename):
			self.open(self.filename)
		else:
			self._image = Image.new(self.default_mode, self.default_size)

		self.draw()

	def open(self, filename):
		logging.debug("Opening image as a template: %s" % filename)

		image = Image.open(filename)
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

	@property
	def font(self):
		if not hasattr(self, "__font"):
			fontfile = os.path.join(
				self.request.application.settings.get("template_path", ""),
				"i-use", "fonts", self._font
			)

			self.__font = ImageFont.truetype(fontfile, self._font_size, encoding="unic")

		return self.__font

	def draw_text(self, pos, text, **kwargs):
		if not kwargs.has_key("font"):
			kwargs["font"] = self.font

		return self.paint.text(pos, text, **kwargs)

	@property
	def filename(self):
		if not self._filename:
			return

		return os.path.join(
			self.request.application.settings.get("template_path", ""),
			"i-use", self._filename
		)

	@property
	def locale(self):
		return self.request.locale


#class Image1(ImageObject):
#	id = 0
#
#	default_size = 500, 50
#
#	def draw(self):
#		# Background
#		self.paint.rectangle(((0, 0), self.default_size), fill="#000000")
#
#		# Release information
#		self.paint.text((10, 10), "%s" % self.profile.release)
#
#		# Hardware information
#		hw = [
#			self.profile.cpu.model_string,
#			"Mem: %.1fG" % (self.profile.memory / 1024**2),
#		]
#
#		if self.profile.virtual:
#			virt = "V-%s" % self.profile.hypervisor.vendor
#			if self.profile.hypervisor.type == "para":
#				virt = "%s-PV" % virt
#			hw.append(virt)
#
#		if self.profile.cpu.capable_64bit:
#			hw.append("64")
#
#		self.paint.text((10, 30), "%s" % " | ".join(hw))
#
#
#IUse().add_imagetype(Image1)


class Image1(ImageObject):
	id = 0

	default_size = 500, 50

	_filename = "i-use-1.png"
	_font = "DejaVuSans-Bold.ttf"
	_font_size = 9

	def draw(self):
		_ = self.locale.translate

		line1 = [self.profile.release,]

		if self.profile.virtual:
			virt = "V-%s" % self.profile.hypervisor.vendor
			if self.profile.hypervisor.type == "para":
				virt = "%s-PV" % virt
			line1.append(virt)

		self.draw_text((225, 8), " | ".join(line1))

		line2 = []
		line2.append(self.profile.cpu.friendly_string)
		line2.append(_("Mem: %s") % self.profile.friendly_memory)

		if self.profile.root_size:
			line2.append(_("Disk: %s") % self.profile.friendly_root_size)

		line3 = []

		if self.profile.network:
			zones = []

			for zone in ("green", "red", "blue", "orange"):
				if self.profile.network.has_zone(zone):
					zones.append(_(zone))

			if zones:
				line3.append(_("Networks: %s") % " | ".join(zones))

		self.draw_text((225, 20), "%s" % " - ".join(line2))
		self.draw_text((225, 32), "%s" % " - ".join(line3))


IUse().add_imagetype(Image1)


if __name__ == "__main__":
	image = Image1("123")
	image.save("picture.png")

