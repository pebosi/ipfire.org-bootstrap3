#!/usr/bin/python

import random

from json import Json

class Banners(Json):
	def __init__(self, lang="en"):
		self.lang = lang
		Json.__init__(self, "banners.json")

	def random(self):
		banner = random.choice(self.json.values())
		return banner

