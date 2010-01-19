#!/usr/bin/python

import tornado.web

import menu
import releases

class UIModule(tornado.web.UIModule):
	def render_string(self, *args, **kwargs):
		kwargs.update({
			"link" : self.handler.link,
		})
		return tornado.web.UIModule.render_string(self, *args, **kwargs)


class MenuItemModule(UIModule):
	def render(self, item):
		if self.request.uri.endswith(item.uri):
			item.active = True

		if not item.uri.startswith("http://"):
			item.uri = "/%s%s" % (self.locale.code[:2], item.uri,)

		if type(item.name) == type({}):
			item.name = item.name[self.locale.code[:2]]

		return self.render_string("modules/menu-item.html", item=item)


class MenuModule(UIModule):
	def render(self, menuclass=None):
		if not menuclass:
			menuclass = menu.Menu("menu.json")
		return self.render_string("modules/menu.html", menuitems=menuclass.items)


class NewsItemModule(UIModule):
	def render(self, item):
		for attr in ("subject", "content"):
			if type(item[attr]) != type({}):
				continue
			item[attr] = item[attr][self.locale.code[:2]]

		return self.render_string("modules/news-item.html", item=item)


#class SidebarModule(UIModule):
#	def render(self, sidebar):
#		return self.render_string("modules/sidebar.html", items=sidebar.items)


class SidebarItemModule(UIModule):
	def render(self):
		return self.render_string("modules/sidebar-item.html")


class SidebarReleaseModule(UIModule):
	releases = releases.Releases()

	def render(self):
		return self.render_string("modules/sidebar-release.html",
			releases=self.releases)


class ReleaseItemModule(UIModule):
	def render(self, item):
		return self.render_string("modules/release-item.html", item=item)


class SidebarBannerModule(UIModule):
	def render(self, item):
		return self.render_string("modules/sidebar-banner.html", item=item)


class BuildModule(UIModule):
	def render(self, build):
		return self.render_string("modules/builds.html", build=build)
