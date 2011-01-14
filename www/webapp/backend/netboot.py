#!/usr/bin/python

from databases import Databases
from misc import Singleton


class MenuEntry(object):
	def __init__(self, _data):
		self._data = _data
		self.submenu = None

	@property
	def id(self):
		return self._data.get("id")

	@property
	def type(self):
		return self._data.get("type", "root")

	@property
	def title(self):
		return self._data.get("title", "")

	@property
	def description(self):
		return self._data.get("description", "")

	@property
	def item(self):
		if self.type == "config":
			return self._data.get("item")

	@property
	def submenu_level(self):
		if self.type == "header":
			return int(self._data.get("item"))


class NetBoot(object):
	__metaclass__ = Singleton

	@property
	def db(self):
		return Databases().webapp

	def get_menu(self, level=0):
		menu = []

		for m in self.db.query("SELECT * FROM boot_menu WHERE level = %d ORDER by level,prio" % level):
			m = MenuEntry(m)

			if m.type == "header":
				m.submenu = self.get_menu(m.submenu_level)

			elif m.type == "config":
				m._data.update(self.db.get("SELECT title, description FROM boot WHERE id = %s" % m.item))

			menu.append(m)

		return menu

	def get_config(self, id):
		id = int(id)
		return self.db.get("SELECT * FROM boot WHERE id = %s", id)
