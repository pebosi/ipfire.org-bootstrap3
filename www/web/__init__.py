#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import cgi
import time

try:
	import cStringIO as StringIO
except ImportError:
	import StringIO

from http import HTTPResponse, WebError

import info
import lang
import menu

class Data:
	def __init__(self):
		self.output = ""
	
	def w(self, s):
		self.output += "%s\n" % s
	
	write = w
		
	def __call__(self):
		return self.output


class Page(object):
	def __init__(self):
		self.io = StringIO.StringIO()

		self.info = info.Info()
		self.langs = lang.Languages()
		self.menu = menu.Menu(self.langs.current)
		self.site = self.title = cgi.FieldStorage().getfirst("site", default="index")

		self.content = None
		self.javascript = None
		self.sidebar = None

	@property
	def data(self):
		ret = { "content" : "",
				 "javascript": "",
				 "lang"   : self.langs.current,
				 "languages" : self.langs.menu(self.site),
				 "menu"   : self.menu(),
				 "name"   : self.info["name"],
				 "server" : os.environ["SERVER_NAME"].replace("ipfire", "<span>ipfire</span>"),
				 "sidebar" : "",
				 "slogan" : self.info["slogan"],
				 "sname"  : self.info["sname"],
				 "title"  : "%s - %s" % (os.environ["SERVER_NAME"], self.title,),				 
				 "year"   : time.strftime("%Y"),}

		if self.content:
			ret["content"] = self.content(self.langs.current)
		if self.javascript:
			ret["javascript"] = self.javascript(self.langs.current)
		if self.sidebar:
			ret["sidebar"] = self.sidebar(self.langs.current)

		return ret
			
	def include(self, file):
		f = open(file)
		output = f.read()
		f.close()
		self.io.write(output % self.data)

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
		h.execute(self.io.getvalue())

		
class Content(Data):
	def __init__(self):
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
