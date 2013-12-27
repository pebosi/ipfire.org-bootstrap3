#!/usr/bin/python

import logging
import os
import tornado.httpserver
import tornado.ioloop
import tornado.locale
import tornado.options
import tornado.web

import backend

from handlers_base import BaseHandler

BASEDIR = os.path.dirname(__file__)

def word_wrap(s, width=45):
	paragraphs = s.split('\n')
	lines = []
	for paragraph in paragraphs:
		while len(paragraph) > width:
			pos = paragraph.rfind(' ', 0, width)
			if not pos:
				pos = width
			lines.append(paragraph[:pos])
			paragraph = paragraph[pos:]
		lines.append(paragraph.lstrip())
	return '\n'.join(lines)

class BootBaseHandler(BaseHandler):
	pass


class MenuGPXEHandler(BootBaseHandler):
	"""
		menu.gpxe
	"""
	def get(self):
		# Check if version of the bootloader is recent enough.
		# Otherwise send the latest version of the PXE loader.
		user_agent = self.request.headers.get("User-Agent", None)
		if user_agent:
			try:
				client, version = user_agent.split("/")
			except:
				pass
			else:
				# We replaced gPXE by iPXE.
				if client == "gPXE":
					return self.serve_update()

				# Everything under version 1.0.0 should be
				# updated.
				if version < "1.0.0":
					return self.serve_update()

		# Devliver content
		self.set_header("Content-Type", "text/plain")
		self.write("#!gpxe\n")

		self.write("set 209:string premenu.cfg\n")
		self.write("set 210:string http://boot.ipfire.org/\n")
		self.write("chain pxelinux.0\n")

	def serve_update(self):
		self.set_header("Content-Type", "text/plain")
		self.write("#!gpxe\n")

		# Small warning
		self.write("echo\necho Your copy of gPXE/iPXE is too old. ")
		self.write("Upgrade to avoid seeing this every boot!\n")

		self.write("chain http://mirror0.ipfire.org/releases/ipfire-boot/latest/ipxe.kpxe\n")


class MenuCfgHandler(BootBaseHandler):
	def get(self):
		self.set_header("Content-Type", "text/plain")

		latest_release = self.releases.get_latest()
		stable_releases = self.releases.get_stable()
		try:
			stable_releases.remove(latest_release)
		except ValueError:
			pass

		development_releases = self.releases.get_unstable()

		self.render("netboot/menu.cfg", latest_release=latest_release,
			stable_releases=stable_releases, development_releases=development_releases)
