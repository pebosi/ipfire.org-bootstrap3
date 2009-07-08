#!/usr/bin/python

from elements import Box
from json import Json

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
