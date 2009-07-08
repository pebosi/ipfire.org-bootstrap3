#!/usr/bin/python

from . import Data
from banners import Banners
from info import Info

class Box(Data):
	def __init__(self, headline, subtitle=""):
		Data.__init__(self)
		self.w("""<div class="post"><h3>%s</h3><a name="%s"></a>""" % (headline,headline,))
		if subtitle:
			self.w("""<div class="post_info">%s</div>""" % (subtitle,))

	def __call__(self):
		self.w("""<br class="clear" /></div>""")
		return Data.__call__(self)

class Sidebar(Data):
	def __init__(self):
		Data.__init__(self)

	def content(self, lang):
		banners = Banners()
		self.w("""<h4>%(title)s</h4><a href="%(link)s" target="_blank">
			<img class="banner" src="%(uri)s" /></a>""" % banners.random())

	def __call__(self, lang):
		self.content(lang)
		return Data.__call__(self)

class Releases(Data):
	def __init__(self):
		Data.__init__(self)
	
	def content(self, lang):
		info = Info()
		if lang == "de":
			self.write("""<h4><span>release</span> informationen</h4>
				<p><strong>Aktuelle Version</strong>:<br />%(stable)s</p>
				<p><strong>Testversionen</strong>:<br />%(testing)s</p>
			""" % info["releases"])
		else:
			self.write("""<h4><span>info</span>rmation</h4>
				<p><strong>Current version</strong>:<br />%(stable)s</p>
				<p><strong>Current unstables</strong>:<br />%(testing)s</p>
			""" % info["releases"])
	
	def __call__(self, lang):
		self.content(lang)
		return Data.__call__(self)
