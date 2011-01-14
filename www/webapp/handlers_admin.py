#!/usr/bin/python

# XXX most of this is broken

import tornado.web

from handlers_base import *

import backend

class AdminBaseHandler(BaseHandler):
	@property
	def accounts(self):
		return backend.Accounts()

	@property
	def planet(self):
		return backend.Planet()

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
	def get(self):
		text = self.get_argument("text", "")

		# Render markup
		self.write(self.planet.render(text))
		self.finish()


class AdminPlanetHandler(AdminBaseHandler):
	@tornado.web.authenticated
	def get(self):
		entries = self.planet.get_entries(limit=100)

		self.render("admin-planet.html", entries=entries)


class AdminPlanetComposeHandler(AdminBaseHandler):
	@tornado.web.authenticated
	def get(self, id=None):
		entry = backend.PlanetEntry()

		if id:
			entry = self.planet.get_entry_by_id(id)

		self.render("admin-planet-compose.html", entry=entry)

	@tornado.web.authenticated
	def post(self, id=None):
		id = self.get_argument("id", id)

		entry = backend.PlanetEntry()

		if id:
			entry = self.planet.get_entry_by_id(id)

		entry.set("title", self.get_argument("title"))
		entry.set("markdown", self.get_argument("markdown"))
		entry.set("author_id", self.current_user)

		if id:
			self.planet.update_entry(entry)
		else:
			self.planet.save_entry(entry)

		self.redirect("/planet")


class AdminPlanetEditHandler(AdminPlanetComposeHandler):
	pass


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
	@property
	def mirrors(self):
		return backend.Mirrors()


class AdminMirrorsHandler(AdminMirrorsBaseHandler):
	@tornado.web.authenticated
	def get(self):
		mirrors = self.mirrors.list()

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
			mirror = self.db.get("SELECT * FROM mirrors WHERE id = '%s'", int(id))
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
		news = self.news.list()

		self.render("admin-news.html", news=news)


class AdminNewsCreateHandler(AdminNewsBaseHandler):
	@tornado.web.authenticated
	def get(self, id=None):
		# if XXX
		
		
		self.render("admin-news-create.html", news=news)


class AdminNewsEditHandler(AdminNewsCreateHandler):
	pass
