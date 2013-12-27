#!/usr/bin/python

import datetime
import tornado.web

from handlers_base import *

import backend

class AdminBaseHandler(BaseHandler):
	def get_current_user(self):
		return self.get_secure_cookie("account")


class AdminLoginHandler(AdminBaseHandler):
	def get(self):
		self.render("admin-login.html")

	def post(self):
		account = self.accounts.search(self.get_argument("name"))
		if not account:
			raise tornado.web.HTTPError(403)

		if account.check_password(self.get_argument("password")):
			self.set_secure_cookie("account", account.uid)
		else:
			raise tornado.web.HTTPError(403)

		self.redirect("/")


class AdminLogoutHandler(AdminBaseHandler):
	def get(self):
		self.clear_cookie("account")
		self.redirect("/")


class AdminIndexHandler(AdminBaseHandler):
	@tornado.web.authenticated
	def get(self):
		self.render("admin-index.html")


class AdminApiPlanetRenderMarkupHandler(AdminBaseHandler):
	@tornado.web.authenticated
	def post(self):
		text = self.get_argument("text", "")

		# Render markup
		output = {
			"html" : self.planet.render(text),
		}
		self.finish(output)


class AdminPlanetHandler(AdminBaseHandler):
	@tornado.web.authenticated
	def get(self):
		entries = self.planet.get_entries(status=None, limit=100)

		self.render("admin-planet.html", entries=entries)


class AdminPlanetComposeHandler(AdminBaseHandler):
	@tornado.web.authenticated
	def get(self, slug=None):
		entry = None

		if slug:
			entry = self.planet.get_entry_by_slug(slug)
			if not entry:
				raise tornado.web.HTTPError(404)

		self.render("admin-planet-compose.html", entry=entry)

	@tornado.web.authenticated
	def post(self):
		title = self.get_argument("title")
		markdown = self.get_argument("markdown")
		tags = self.get_argument("tags", "")

		status = self.get_argument("status", "draft")
		assert status in ("draft", "published")

		author = self.accounts.find(self.current_user)

		entry = self.planet.create(title=title, markdown=markdown,
			author=author, status=status, tags=tags.split())

		self.redirect("/planet")


class AdminPlanetEditHandler(AdminPlanetComposeHandler):
	@tornado.web.authenticated
	def post(self, slug):
		entry = self.planet.get_entry_by_slug(slug)
		if not entry:
			raise tornado.web.HTTPError(404)

		entry.title = self.get_argument("title")
		entry.markdown = self.get_argument("markdown")
		entry.tags = self.get_argument("tags", "").split()

		entry.status = self.get_argument("status", "draft")

		self.redirect("/planet")


class AdminPlanetPublishHandler(AdminBaseHandler):
	@tornado.web.authenticated
	def get(self, slug):
		entry = self.planet.get_entry_by_slug(slug)
		if not entry:
			raise tornado.web.HTTPError(404)

		entry.status = "published"
		entry.published = datetime.datetime.utcnow()

		self.redirect("/planet")


class AdminAccountsBaseHandler(AdminBaseHandler):
	pass


class AdminAccountsHandler(AdminAccountsBaseHandler):
	@tornado.web.authenticated
	def get(self):
		accounts = self.accounts.list()
		self.render("admin-accounts.html", accounts=accounts)


class AdminAccountsEditHandler(AdminAccountsBaseHandler):
	@tornado.web.authenticated
	def get(self, id):
		account = self.accounts.search(id)
		if not account:
			raise tornado.web.HTTPError(404)

		self.render("admin-accounts-edit.html", account=account)


class AdminAccountsDeleteHandler(AdminAccountsBaseHandler):
	@tornado.web.authenticated
	def get(self, id):
		account = self.accounts.search(id)
		if not account:
			raise tornado.web.HTTPError(404)

		self.accounts.delete(id)
		self.redirect("/accounts")


class AdminMirrorsBaseHandler(AdminBaseHandler):
	pass


class AdminMirrorsHandler(AdminMirrorsBaseHandler):
	@tornado.web.authenticated
	def get(self):
		mirrors = self.mirrors.get_all()

		self.render("admin-mirrors.html", mirrors=mirrors)


class AdminMirrorsUpdateHandler(AdminMirrorsBaseHandler):
	@tornado.web.authenticated
	def get(self):
		self.mirrors.check_all()
		self.redirect("/mirrors")


class AdminMirrorsCreateHandler(AdminMirrorsBaseHandler):
	@tornado.web.authenticated
	def get(self, id=None):
		if id:
			mirror = self.db.get("SELECT * FROM mirrors WHERE id = %s", id)
		else:
			mirror = tornado.database.Row(
				id="",
				hostname="",
				owner="",
				location="",
				path="/",
				releases="Y",
				pakfire2="Y",
				pakfire3="Y",
				disabled="N"
			)

		self.render("admin-mirrors-create.html", mirror=mirror)

	@tornado.web.authenticated
	def post(self, id=None):
		args = tornado.database.Row()
		for key in ("id", "hostname", "owner", "location", "path", "releases",
				"pakfire2", "pakfire3", "disabled"):
			args[key] = self.get_argument(key, "")

		if args.id:
			if not self.mirrors.get(args.id):
				raise tornado.web.HTTPError(404)

			#self.db.execute("""UPDATE mirrors SET
			#	hostname = %s, owner = %s, location = %s, path = %s, mirror = %s,
			#	pakfire2 = %s, pakfire3 = %s, disabled = %s
			#	WHERE id = %s""", args.hostname, args.owner, args.location,
			#	args.path, args.mirror, args.pakfire2, args.pakfire3, args.disabled,
			#	args.id)
			self.db.update("mirrors", args.id, **args)

		else:
			#self.db.execute("""INSERT INTO
			#	mirrors(hostname, owner, location, path, mirror, pakfire2, pakfire3, disabled)
			#	VALUES(%s, %s, %s, %s, %s, %s, %s, %s)""", args.hostname, args.owner,
			#	args.location, args.path, args.mirror, args.pakfire2, args.pakfire3, args.disabled)
			self.db.insert("mirrors", **args)

		# Update database information
		self.mirrors.check_all()

		self.redirect("/mirrors")


class AdminMirrorsEditHandler(AdminMirrorsCreateHandler):
	pass


class AdminMirrorsDeleteHandler(AdminMirrorsBaseHandler):
	@tornado.web.authenticated
	def get(self, id):
		self.db.execute("DELETE FROM mirrors WHERE id=%s", id)
		self.db.execute("DELETE FROM mirror_files WHERE mirror=%s", id)
		self.redirect("/mirrors")


class AdminMirrorsDetailsHandler(AdminMirrorsBaseHandler):
	@tornado.web.authenticated
	def get(self, id):
		mirror = self.mirrors.get(id)
		if not mirror:
			raise tornado.web.HTTPError(404)

		self.render("admin-mirrors-details.html", mirror=mirror)


class AdminNewsBaseHandler(AdminBaseHandler):
	@property
	def news(self):
		return self.backend.news


class AdminNewsHandler(AdminNewsBaseHandler):
	@tornado.web.authenticated
	def get(self):
		news = self.news.get_all()

		self.render("admin-news.html", news=news)


class AdminNewsCreateHandler(AdminNewsBaseHandler):
	@tornado.web.authenticated
	def get(self, id=None):
		# if XXX
		
		
		self.render("admin-news-create.html", news=news)


class AdminNewsEditHandler(AdminNewsCreateHandler):
	pass


class AdminDownloadsHandler(AdminBaseHandler):
	@tornado.web.authenticated
	def get(self):
		self.render("admin-downloads.html",
			downloads_total = self.downloads.total,
			downloads_today = self.downloads.today,
			downloads_yesterday = self.downloads.yesterday,
			downloads_locations_today = self.downloads.get_countries("today"),
			downloads_locations_total = self.downloads.get_countries(),
		)


class AdminDownloadsMirrorsHandler(AdminBaseHandler):
	@tornado.web.authenticated
	def get(self):
		self.render("admin-downloads-mirrors.html",
			mirror_load_total = self.downloads.get_mirror_load(),
			mirror_load_today = self.downloads.get_mirror_load("today"),
		)
