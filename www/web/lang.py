#!/usr/bin/python

import cgi

class Languages:
	def __init__(self, doc=""):
		self.available = []

		for lang in ("de", "en",):
			self.append(lang,)
		
		self.current = cgi.FieldStorage().getfirst("lang") or "en"

	def append(self, lang):
		self.available.append(lang)

	def menu(self, doc):
		s = ""
		for lang in self.available:
			s += """<a href="/%(lang)s/%(doc)s"><img src="/images/%(lang)s.gif" alt="%(lang)s" /></a>""" % \
				{ "lang" : lang, "doc" : doc, }
		return s
