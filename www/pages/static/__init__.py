#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from xml.dom.minidom import parseString

import web
from web.banners import Banners
from web.elements import Box, Releases
from web.news import News

class Xml(object):
	def __init__(self, file):
		file = "%s/pages/static/%s.xml" % (os.getcwd(), file,)
		f = open(file)
		data = f.read()
		f.close()

		self.xml = parseString(data).getElementsByTagName("Site")[0]

	def getAttribute(self, node, attr):
		return node.getAttribute(attr).strip()

	def getText(self, node):
		ret = ""
		for i in node.childNodes:
			ret += i.data
		return ret.encode("utf-8")


class Content(Xml):
	def __init__(self, file,):
		Xml.__init__(self, file)

	def __call__(self, lang="en"):
		ret = ""
		for paragraphs in self.xml.getElementsByTagName("Paragraphs"):
			for paragraph in paragraphs.getElementsByTagName("Paragraph"):
				if self.getAttribute(paragraph, "news") == "1":
					news = News(int(self.getAttribute(paragraph, "count")))
					ret += news(lang).encode("utf-8")
					continue

				# Heading
				for heading in paragraph.getElementsByTagName("Heading"):
					if self.getAttribute(heading, "lang") == lang or \
							not self.getAttribute(heading, "lang"):
						heading = self.getText(heading)
						break

				b = Box(heading)

				# Content
				for content in paragraph.getElementsByTagName("Content"):
					if self.getAttribute(content, "lang") == lang or \
							not self.getAttribute(content, "lang"):
						if self.getAttribute(content, "raw") == "1":
							s = self.getText(content)
						else:
							s = "<p>%s</p>" % self.getText(content)
						b.w(s)
				
				ret += b()
		return ret


class Sidebar(Xml):
	def __init__(self, file):
		Xml.__init__(self, file)

	def __call__(self, lang="en"):
		ret = ""
		sidebar = self.xml.getElementsByTagName("Sidebar")[0]
		for paragraph in sidebar.getElementsByTagName("Paragraph"):
			if self.getAttribute(paragraph, "banner") == "1":
				b = Banners()
				ret += """<h4>%(title)s</h4><a href="%(link)s" target="_blank">
						<img class="banner" src="%(uri)s" /></a>""" % b.random()
				continue
			elif self.getAttribute(paragraph, "releases") == "1":
				r = Releases()
				ret += r(lang)
				continue

			# Heading
			for heading in paragraph.getElementsByTagName("Heading"):
				if self.getAttribute(heading, "lang") == lang or \
						not self.getAttribute(heading, "lang"):
					heading = self.getText(heading)
					break

			ret += "<h4>%s</h4>" % heading

			# Content
			for content in paragraph.getElementsByTagName("Content"):
				if self.getAttribute(content, "lang") == lang or \
						not self.getAttribute(content, "lang"):
					if self.getAttribute(content, "raw") == "1":
						s = self.getText(content)
					else:
						s = "<p>%s</p>" % self.getText(content)
					ret += s

		return ret

page = web.Page()
page.content = Content(page.site)
page.sidebar = Sidebar(page.site)
