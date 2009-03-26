#!/usr/bin/python

import sys
import cgi
import imputil

from web import Page

site = cgi.FieldStorage().getfirst("site") or "main"

sys.path = [ "pages",] + sys.path
for page in (site, "static"):
	try:
		found = imputil.imp.find_module(page)
		loaded = imputil.imp.load_module(page, found[0], found[1], found[2])
		content = loaded.__dict__["Content"]
		sidebar = loaded.__dict__["Sidebar"]
		break
	except ImportError, e:
		pass

c = content(site)
s = sidebar(site)

p = Page(site, c, s)
p()
