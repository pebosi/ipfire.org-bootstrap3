#!/usr/bin/python

import os

import web
import web.elements
from web.javascript import Javascript

BASE="/srv/checkout"

projects = []

class Po(object):
	code2lang = {
		"da" : "Dansk (Dansk)",
		"de" : "Deutsch (German)",
		"fr" : "Français (French)",
	}

	def __init__(self, path):
		self.path = path
		
		p = os.popen("msgfmt -v --statistics %s 2>&1" % self.path)
		self.line = p.readlines()[0]

	def __cmp__(self, other):
		return cmp(self.lang, other.lang)

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
					self._translations.append(Po(os.path.join(self.path, path)))
		return self._translations

	def find_pot(self):
		for path in os.listdir(self.path):
			if path.endswith(".pot"):
				self.pot = Po(os.path.join(self.path, path))
				break


projects.append(Project("pomona", BASE + "/ipfire-3.x/src/pomona/po", name="Pomona", desc="The pomona installer for ipfire."))

class Content(web.Content):
	def __init__(self):
		web.Content.__init__(self)
		self.projects = projects
		
	def __call__(self, lang):
		ret = """<h3>IPFire Translation Status</h3>
					<div id="tabs"><ul>"""
		
		for project in self.projects:
			ret += """<li><a href="#%s">%s</a></li>""" % (project.id, project.name)
		
		ret += "</ul>"
		
		for project in self.projects:
			ret += """<div id="%s">
				<p><strong>Description:</strong> %s</p>
				<br />
				<table class="translate">
					<tr>
						<th>Language</th>
						<th>Translated</th>
						<th>Untranslated</th>
						<th>Fuzzy</th>
						<th>Status</th>
					</tr>""" % (project.id, project.desc)

			total = 0
			if project.pot:
				total = project.pot.untranslated

			for t in sorted(project.translations):
				if total:
					percent = "%3.1f%%" % (t.translated * 100 / total)
				else:
					percent = "---.-%"

				ret += """\
					<tr>
						<td class="lang"><img src="/images/flags/%s.png" alt="%s" />%s</td>
						<td>%s</td>
						<td>%s</td>
						<td>%s</td>
						<td>%s</td>
					</tr>""" % \
					(t.code, t.code, t.lang, t.translated, t.untranslated, t.fuzzy, percent)

			ret += "</table>"

			if project.pot:
				ret += """\
					<p>
						<br />
						<strong>Template</strong> - %s strings
					</p>""" % project.pot.untranslated

			ret += "</div>"

		ret += "</div>"
		return ret

page = web.Page()
page.content = Content()
page.sidebar = web.elements.DevelopmentSidebar()
page.javascript = Javascript(1, 1)
page.javascript.write("""
	<script type="text/javascript">
		$(function() {
			$("#tabs").tabs();
		});
	</script>
""")
