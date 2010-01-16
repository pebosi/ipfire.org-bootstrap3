#!/usr/bin/python

import os

import tornado.locale

class Po(object):
	def __init__(self, path, project):
		self.path = path
		self.project = project
		
		p = os.popen("msgfmt -v --statistics %s 2>&1" % self.path)
		self.line = p.readlines()[0]

	def __cmp__(self, other):
		return cmp(self.lang, other.lang)

	@property
	def code2lang(self):
		ret = {}
		for lang in tornado.locale.LOCALE_NAMES.keys():
			ret[lang[:2]] = "%(name)s (%(name_en)s)" % tornado.locale.LOCALE_NAMES[lang]
		return ret

	@property
	def code(self):
		return os.path.basename(self.path)[:-3]

	@property
	def lang(self):
		return self.code2lang.get(self.code, "Unknown (%s)" % self.code)

	@property
	def translated(self):
		return int(self.line.split()[0])

	@property
	def untranslated(self):
		l = self.line.split()
		if len(l) == 6:
			return int(l[3])
		elif len(l) == 9:
			return int(l[6])
		return 0

	@property
	def fuzzy(self):
		l = self.line.split()
		if len(l) == 9:
			return l[3]
		return 0

	@property
	def percent(self):
		if not self.project.total_strings:
			return "---.-- %"
		
		return "%3.1f%%" % (self.translated * 100 / self.project.total_strings)


class Project(object):
	def __init__(self, id, path, **kwargs):
		self.id = id
		self.path = path
		self._name = kwargs.pop("name")
		self.desc = kwargs.pop("desc")

		self._translations = []
		self.pot = None
		self.find_pot()

	@property
	def name(self):
		if self._name:
			return self._name
		return self.id

	@property
	def translations(self):
		if not self._translations:
			for path in os.listdir(self.path):
				if path.endswith(".po"):
					self._translations.append(Po(os.path.join(self.path, path), self))
			self._translations.sort()
		return self._translations

	def find_pot(self):
		for path in os.listdir(self.path):
			if path.endswith(".pot"):
				self.pot = Po(os.path.join(self.path, path), self)
				break

	@property
	def total_strings(self):
		if not self.pot:
			return 0
		return self.pot.untranslated

projects = [
	Project("pomona", "/srv/checkout/ipfire-3.x/src/pomona/po",
		name="Pomona", desc="The pomona installer for ipfire."),
]
