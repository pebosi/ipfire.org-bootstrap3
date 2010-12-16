#!/usr/bin/python

import logging
import socket
import textile
import tornado.escape
import tornado.web

from tornado.database import Row

import backend

class UIModule(tornado.web.UIModule):
	@property
	def accounts(self):
		return self.handler.accounts

	@property
	def banners(self):
		return self.handler.banners

	@property
	def releases(self):
		return self.handler.releases


class MenuModule(UIModule):
	def render(self):
		hostname = self.request.host.lower().split(':')[0]

		menuitems = []
		for m in backend.Menu().get(hostname):
			m.active = False

			if m.uri and self.request.uri.endswith(m.uri):
				m.active = True

			# Translate the description of the link
			m.description = \
				self.locale.translate(m.description)
			m.description = tornado.escape.xhtml_escape(m.description)

			menuitems.append(m)

		return self.render_string("modules/menu.html", menuitems=menuitems)


class NewsItemModule(UIModule):
	def get_author(self, author):
		# Get name of author
		author = self.accounts.find(author)
		if author:
			return author.cn
		else:
			_ = self.locale.translate
			return _("Unknown author")

	def render(self, item, uncut=False):
		# Get author
		item.author = self.get_author(item.author_id)

		if not uncut and len(item.text) >= 400:
			item.text = item.text[:400] + "..."

		# Render text
		item.text = textile.textile(item.text)

		return self.render_string("modules/news-item.html", item=item, uncut=uncut)


class NewsLineModule(NewsItemModule):
	def render(self, item):
		return self.render_string("modules/news-line.html", item=item)


class MirrorItemModule(UIModule):
	def render(self, item):
		return self.render_string("modules/mirror-item.html", item=item)


class SidebarItemModule(UIModule):
	def render(self):
		return self.render_string("modules/sidebar-item.html")


class SidebarReleaseModule(UIModule):
	def render(self):
		return self.render_string("modules/sidebar-release.html",
			latest=self.releases.get_latest())


class ReleaseItemModule(UIModule):
	def render(self, item):
		return self.render_string("modules/release-item.html", release=item)


class SidebarBannerModule(UIModule):
	def render(self, item=None):
		if not item:
			item = self.banners.get_random()

		return self.render_string("modules/sidebar-banner.html", item=item)


class PlanetEntryModule(UIModule):
	def render(self, entry, short=False):
		return self.render_string("modules/planet-entry.html",
			entry=entry, short=short)


class TrackerPeerListModule(UIModule):
	def render(self, peers, percentages=False):
		# Guess country code and hostname of the host
		for peer in peers:
			country_code = backend.GeoIP().get_country(peer["ip"])
			peer["country_code"] = country_code or "unknown"

			try:
				peer["hostname"] = socket.gethostbyaddr(peer["ip"])[0]
			except:
				peer["hostname"] = ""

		return self.render_string("modules/tracker-peerlist.html",
			peers=[Row(p) for p in peers], percentages=percentages)


class StasyTableModule(UIModule):
	def render(self, items):
		hundred_percent = 0
		for v in items.values():
			hundred_percent += v

		if hundred_percent:
			_items = []
			for k in sorted(items.keys()):
				v = float(items[k] * 100) / hundred_percent
				_items.append((k, v))
			items = _items

		print items

		return self.render_string("modules/stasy-table.html", items=items)
