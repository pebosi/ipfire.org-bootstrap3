#!/usr/bin/python

import logging
import os
import tornado.httpserver
import tornado.ioloop
import tornado.locale
import tornado.options
import tornado.web

import backend

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

class BootBaseHandler(tornado.web.RequestHandler):
	@property
	def netboot(self):
		return backend.NetBoot()


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
	def _menu_string(self, menu, level=0):
		s = ""

		for entry in menu:
			s += self._menu_entry(entry, level=level)

		return s

	def _menu_entry(self, entry, level=0):
		lines = []

		ident = "\t" * level

		if entry.type == "seperator":
			lines.append(ident + "menu separator")

		elif entry.type == "header":
			lines.append(ident + "menu begin %d" % entry.id)
			lines.append(ident + "\tmenu title %s" % entry.title)

			# Add "Back..." entry
			lines.append(ident + "\tlabel %d.back" % entry.id)
			lines.append(ident + "\t\tmenu label Back...")
			lines.append(ident + "\t\tmenu exit")
			lines.append(ident + "\tmenu separator")

			lines.append("%s" % self._menu_string(entry.submenu, level=level+1))
			lines.append(ident + "menu end")

		elif entry.type == "config":
			lines.append(ident + "label %d" % entry.id)
			lines.append(ident + "\tmenu label %s" % entry.title)
			if entry.description:
				lines.append(ident + "\ttext help")
				lines.append(word_wrap(entry.description))
				lines.append(ident + "\tendtext")

			config = self.netboot.get_config(entry.item)
			if not config: return ""

			lines.append(ident + "\tkernel %s" % config.image1)
			if config.image2:
				lines.append(ident + "\tinitrd %s" % config.image2)
			if config.args:
				lines.append(ident + "\tappend %s" % config.args)

		return "\n".join(lines + [""])

	def get(self):
		self.set_header("Content-Type", "text/plain")

		menu = self._menu_string(self.netboot.get_menu(1))

		self.render("netboot/menu.cfg", menu=menu)


class BootGPXEHandler(BootBaseHandler):
	def get(self, id):
		config = self.netboot.get_config(id)
		if not config:
			raise tornado.web.HTTPError(404, "Configuration with ID '%s' was not found" % id)

		lines = ["#!gpxe", "imgfree",]

		line = "kernel -n img %s" % config.image1
		if line.endswith(".iso"):
			line += " iso"
		if config.args:
			line += " %s" % config.args
		lines.append(line)

		if config.image2:
			lines.append("initrd -n img %s" % config.image2)

		lines.append("boot img")

		for line in lines:
			self.write("%s\n" % line)
