#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import cgi

sys.path.append(os.environ['DOCUMENT_ROOT'])

import xml.dom.minidom

class Error404(Exception):
	pass

class Error500(Exception):
	pass

class SItem:
	def __init__(self, xml, page, lang):
		self.xml  = xml
		self.page = page
		self.lang = lang

		self.data = u""

	def write(self, s):
		self.data += s #.encode("utf-8")

	def read(self):
		return self.data


class Menu(SItem):
	def __init__(self, file, page, lang):
		SItem.__init__(self, Xml(file, lang), page, lang)
		self.xml.load()

		self.items = XItem(self.xml.dom).childs("Item")

	def __call__(self):
		self.write("""<div id="menu"><ul>""")
		for item in self.items:
			uri = item.attr("uri")
			active = ""
			if self.page == uri:
				active = "class=\"active\""
			
			if not uri.startswith("http://"):
				uri = "/%s/%s" % (uri, self.lang)

			for name in item.childs("Name"):
				if name.attr("lang") in (self.lang, ""):
					self.write("<li><a %s href=\"%s\">%s</a></li>" % \
						(active, uri, name.text()))
		self.write("</ul></div>")
		return self.read()


class Body(SItem):
	def __init__(self, xml, page, lang):
		SItem.__init__(self, xml, page, lang)

		self.paragraphs = XItem(self.xml.dom, "Paragraphs").childs("Paragraph")
		
		self.news = News("news", self.page, self.lang)

	def __call__(self):
		self.write("""<div id="primaryContent_2columns">
			<div id="columnA_2columns">""")
		for paragraph in self.paragraphs:
			for heading in paragraph.childs("Heading"):
				if heading.attr("lang") in (self.lang, ""):
					self.write("<h3>" + heading.text() + "</h3>")	
			for content in paragraph.childs("Content"):
				if content.attr("lang") in (self.lang, ""):
					if content.attr("raw"):
						self.write(content.text())
					else:
						self.write("<p>" + content.text() + "</p>\n")
			self.write("""<br class="clear" />\n""")

		if self.page in ("index", "news",):
			self.write(self.news(3))
		self.write("""</div></div>""")
		return self.read()


class News(SItem):
	def __init__(self, file, page, lang):
		SItem.__init__(self, Xml(file, lang), page, lang)
		self.xml.load()

		self.posts = XItem(self.xml.dom).childs("Posts")

	def __call__(self, limit=None):
		a = 1
		for post in self.posts:
			self.write("""<div class="post">""")
			for id in post.childs("Id"):
				self.write("""<a name="%s"></a>""" % id.text())
			for heading in post.childs("Heading"):
				if heading.attr("lang") in (self.lang, ""):
					self.write("""<h3>%s - %s</h3>""" % (post.childs("Date")[0].text(), heading.text()))
			for subtitle in post.childs("Subtitle"):
				if subtitle.attr("lang") in (self.lang, ""):
					self.write("""<ul class="post_info">
						<li class="date">%s</li></ul>""" % \
							subtitle.text())
			for content in post.childs("Content"):
				if content.attr("lang") in (self.lang, ""):
					if content.attr("raw"):
						self.write(content.text())
					else:
						self.write("<p>" + content.text() + "</p>\n")
			self.write("""</div>""")
			a += 1
			if limit and a > limit:
				break
		return self.read()


class Sidebar(SItem):
	def __init__(self, xml, page, lang):
		SItem.__init__(self, xml, page, lang)

		self.paragraphs = XItem(self.xml.dom, "Sidebar").childs("Paragraph")

	def __call__(self):
		self.write("""<div id="secondaryContent_2columns">
			<div id="columnC_2columns">""")
		for post in self.paragraphs:
			for heading in post.childs("Heading"):
				if heading.attr("lang") in (self.lang, ""):
					self.write("<h4>" + heading.text() + "</h4>")
			for content in post.childs("Content"):
				if content.attr("lang") in (self.lang, ""):
					if content.attr("raw"):
						self.write(content.text())
					else:
						self.write("<p>" + content.text() + "</p>\n")
		self.write("""</div></div>""")
		return self.read()


class XItem:
	def __init__(self, dom, node=None):
		self.dom = self.node = dom
		if node:
			self.node = self.dom.getElementsByTagName(node)[0]
		self.lang = lang

	def attr(self, name):
		return self.node.getAttribute(name).strip()

	def text(self):
		ret = ""
		for i in self.node.childNodes:
			ret = ret + i.data
		return ret

	def element(self, name):
		return XItem(self.node, name)

	def childs(self, name):
		ret = []
		for i in self.node.getElementsByTagName(name):
			ret.append(XItem(i))
		return ret


class Xml:
	def __init__(self, page, lang):
		self.page = page
		self.lang = lang

		self.path = None
		
		self.data = None
		self.dom  = None
		
		self._config = {}

	def load(self):
		self.path = \
			os.path.join(os.environ['DOCUMENT_ROOT'], "data/%s.xml" % self.page)
		try:
			f = open(self.path)
			self.data = f.read()
			f.close()
			self.dom = \
				xml.dom.minidom.parseString(self.data).getElementsByTagName("Site")[0]
		except IOError:
			#self.page = "404"
			#self.load()
			raise Error404
		except:
			#self.page = "500"
			#self.load()
			raise

	def config(self):
		elements = ("Title", "Columns",)
		for element in elements:
			self._config[element.lower()] = ""

		config = XItem(self.dom, "Config")
		for element in elements:
			for lang in config.childs(element):
				if lang.attr("lang") == self.lang:
					self._config[element.lower()] = lang.text()
		return self._config


class Site:
	def __init__(self, page, lang="en"):
		self.code = "200 - OK"
		self.mime = "text/html"

		self.page = page
		self.lang = lang
		self.xml = Xml(page=page, lang=lang)

		self.data = u""
		
		self.menu = Menu("../menu", self.page, self.lang)

		self.config = { "document_name" : page,
						"lang" : self.lang,
						"menu" : self.menu() }
		
		try:
			self.xml.load()
		except Error404:
			self.code = "404 - Not found"
		#except:
		#	self.code = "500 - Internal Server Error"

	def write(self, s):
		self.data += s #.encode("utf-8")

	def include(self, file):
		f = open(file)
		data = f.read()
		f.close()
		self.write(data % self.config)

	def prepare(self):
		for key, val in self.xml.config().items():
			self.config[key] = val
		
		self.config["title"] = "%s - %s" % \
			(os.environ["SERVER_NAME"], self.config["title"],)
		
		self.body = Body(self.xml, self.page, self.lang)
		self.sidebar = Sidebar(self.xml, self.page, self.lang)

	def run(self):
		# First, return the http header
		print "Status: %s" % self.code
		print "Content-Type: %s" % self.mime
		print # End header

		# Include the site's header
		self.include("header.inc")
		
		# Import body and side elements
		self.write(self.body())
		self.write(self.sidebar())

		# Include the site's footer
		self.include("footer.inc")
		
		return self.data.encode("utf-8")


page = cgi.FieldStorage().getfirst("page")
lang = cgi.FieldStorage().getfirst("lang")

if not lang:
	lang = "en"

site = Site(page=page, lang=lang)
site.prepare()

print site.run()
