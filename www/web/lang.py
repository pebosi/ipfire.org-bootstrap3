#!/usr/bin/python

import locale
import cgi

lang2locale = { "de" : "de_DE.utf8",
				"en" : "en_US.utf8", }

class Languages:
	def __init__(self, doc=""):
		self.available = []

		for lang in ("de", "en",):
			self.append(lang,)
		
		self.current = cgi.FieldStorage().getfirst("lang") or "en"
		if lang2locale.has_key(self.current):
			locale.setlocale(locale.LC_ALL, lang2locale[self.current])

	def append(self, lang):
		self.available.append(lang)

	def menu(self, doc):
		s = ""
		for lang in self.available:
			s += """<a href="/%(lang)s/%(doc)s"><img src="/images/%(lang)s.gif" alt="%(lang)s" /></a>""" % \
				{ "lang" : lang, "doc" : doc, }
		return s
