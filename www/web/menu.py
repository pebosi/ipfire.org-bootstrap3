#!/usr/bin/python

import os

from json import Json

class Menu(Json):
	def __init__(self, lang):
		self.lang = lang
		Json.__init__(self, "menu.json")

	def __call__(self):
		s = """<div id="menu"><ul>\n"""
		for item in self.json.values():
			item["active"] = ""

			# Grab language
			if type(item["name"]) == type({}):
				item["name"] = item["name"][self.lang]

			# Add language attribute to local uris
			if item["uri"].startswith("/"):
				item["uri"] = "/%s%s" % (self.lang, item["uri"],)

			if os.environ["REQUEST_URI"].endswith(item["uri"]):
				item["active"] = "class=\"active\""

			s += """<li><a href="%(uri)s" %(active)s>%(name)s</a></li>\n""" % item
		s += "</ul></div>"
		return s
