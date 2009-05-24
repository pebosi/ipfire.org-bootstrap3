#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import cgi
import time
import random
import simplejson as json

from http import HTTPResponse, WebError

import cgitb
cgitb.enable()

class Data:
	def __init__(self):
		self.output = ""
	
	def w(self, s):
		self.output += "%s\n" % s
		
	def __call__(self):
		return self.output


class Json:
	def __init__(self, file):
		f = open(file)
		data = f.read()
		data = data.replace('\n', '') # Remove all \n
		data = data.replace('\t', ' ') # Remove all \t
		self.json = json.loads(data)
		f.close()


class Page(Data):
	def include(self, file):
		f = open(file)
		output = f.read()
		f.close()
		self.w(output % self.data)

	def menu(self):
		m = Menu(self.langs.current)
		return m()

	def __init__(self, title, content, sidebar=None):
		self.output  = ""
		self.title   = title
		self.langs   = Languages()
		self.data    = {"server": os.environ["SERVER_NAME"].replace("ipfire", "<span>ipfire</span>"),
						"title" : "%s - %s" % (os.environ["SERVER_NAME"], title,),
						"menu"  : self.menu(),
						"document_name" : title,
						"lang"  : self.langs.current,
						"languages" : self.langs.menu(title),
						"year"  : time.strftime("%Y"),
						"slogan" : "Security today!",
						"content" : content(self.langs.current),
						"sidebar" : "", }
		if sidebar:
			self.data["sidebar"] = sidebar(self.langs.current)

	def __call__(self):
		type = "text/html"
		try:
			if self.title.endswith(".rss"):
				self.include("rss.inc")
				type = "application/rss+xml"
			else:
				self.include("template.inc")
			code = 200
		except WebError:
			code = 500
		h = HTTPResponse(code, type=type)
		h.execute(self.output)


class News(Json):
	def __init__(self, limit=3):
		Json.__init__(self, "news.json")
		self.news = []
		for key in sorted(self.json.keys()):
			self.news.insert(0, self.json[key])
		if limit:
			self.news = self.news[:limit]

	def html(self, lang="en"):
		s = ""
		for item in self.news:
			for i in ("content", "subject",):
				if type(item[i]) == type({}):
					item[i] = item[i][lang]
			b = Box(item["subject"], "%(date)s - by %(author)s" % item)
			b.w(item["content"])
			if item["link"]:
				if lang == "en":
					b.w("""<p><a href="%(link)s" target="_blank">Read more.</a></p>""" % item)
				elif lang == "de":
					b.w("""<p><a href="%(link)s" target="_blank">Mehr Informationen.</a></p>""" % item)
			s += b()
		return s

	__call__ = html

	def headlines(self, lang="en"):
		headlines = []
		for item in self.news:
			if type(item["subject"]) == type({}):
				item["subject"] = item["subject"][lang]
			headlines.append((item["subject"],))
		return headlines

	def items(self):
		return self.news


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


class Banners(Json):
	def __init__(self, lang="en"):
		self.lang = lang
		Json.__init__(self, "banners.json")

	def random(self):
		banner = random.choice(self.json.values())
		return banner


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
	def __init__(self, name):
		Data.__init__(self)

	def content(self, lang):
		#self.w("""<h4>Test Page</h4>
		#	<p>Lorem ipsum dolor sit amet, consectetuer sadipscing elitr,
		#	sed diam nonumy eirmod tempor invidunt ut labore et dolore magna
		#	aliquyam erat, sed diam voluptua. At vero eos et accusam et justo
		#	duo dolores et ea rebum.</p>""")
		banners = Banners()
		self.w("""<h4>%(title)s</h4><a href="%(link)s" target="_blank">
			<img class="banner" src="%(uri)s" /></a>""" % banners.random())

	def __call__(self, lang):
		self.content(lang)
		return Data.__call__(self)


class Content(Data):
	def __init__(self, name):
		Data.__init__(self)

	def content(self):
		self.w("""<h3>Test Page</h3>
			<p>Lorem ipsum dolor sit amet, consectetuer sadipscing elitr,
			sed diam nonumy eirmod tempor invidunt ut labore et dolore magna
			aliquyam erat, sed diam voluptua. At vero eos et accusam et justo
			duo dolores et ea rebum. Stet clita kasd gubergren, no sea takimata
			sanctus est Lorem ipsum dolor sit amet. Lorem ipsum dolor sit amet,
			consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt
			ut labore et dolore magna aliquyam erat, sed diam voluptua. At vero
			eos et accusam et justo duo dolores et ea rebum. Stet clita kasd
			gubergren, no sea takimata sanctus est Lorem ipsum dolor sit amet.
			Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam
			nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat,
			sed diam voluptua. At vero eos et accusam et justo duo dolores et ea
			rebum. Stet clita kasd gubergren, no sea takimata sanctus est Lorem
			ipsum dolor sit amet.</p>""")
		
		b = Box("Test box one", "Subtitle of box")
		b.write("""<p>Duis autem vel eum iriure dolor in hendrerit in vulputate velit
			esse molestie consequat, vel illum dolore eu feugiat nulla facilisis
			at vero eros et accumsan et iusto odio dignissim qui blandit praesent
			luptatum zzril delenit augue duis dolore te feugait nulla facilisi.
			Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed diam
			nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam erat
			volutpat.</p>""")
		self.w(b())

		b = Box("Test box two", "Subtitle of box")
		b.write("""<p>Ut wisi enim ad minim veniam, quis nostrud exerci tation ullamcorper
			suscipit lobortis nisl ut aliquip ex ea commodo consequat. Duis autem
			vel eum iriure dolor in hendrerit in vulputate velit esse molestie
			consequat, vel illum dolore eu feugiat nulla facilisis at vero eros
			et accumsan et iusto odio dignissim qui blandit praesent luptatum
			zzril delenit augue duis dolore te feugait nulla facilisi.</p>""")
		self.w(b())

	def __call__(self, lang="en"):
		self.content()
		return Data.__call__(self)
