#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
from urllib import quote

import web
import web.news

class Content(web.Content):
	def __init__(self):
		web.Content.__init__(self)
		
		self.news = web.news.News(15)

	def __call__(self, lang="en"):
		s = ""
		for item in self.news.items():
			for i in ("content", "subject",):
				if type(item[i]) == type({}):
					item[i] = item[i][lang]
				item[i] = item[i].encode("utf-8")
			item["lang"] = lang
			item["date"] = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.strptime(item["date"], "%Y-%m-%d"))
			item["guid"] = "http://www.ipfire.org/%s/news#%s" % (lang, quote(item["subject"]))
			s += """<item>
				<title>%(subject)s</title>
				<link>http://www.ipfire.org/%(lang)s/news</link>
				<author>%(mail)s (%(author)s)</author>
				<guid>%(guid)s</guid>
				<pubDate>%(date)s</pubDate>
				<description>
					<![CDATA[
						%(content)s
					]]>
				</description>
			</item>\n""" % item
		return s

page = web.Page()
page.content = Content()
