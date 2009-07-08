#!/usr/bin/python

import cgitb
cgitb.enable()

import sys
import cgi
import imputil

site = cgi.FieldStorage().getfirst("site") or "index"

sys.path = [ "pages",] + sys.path
for s in (site, "static"):
	try:
		found = imputil.imp.find_module(s)
		loaded = imputil.imp.load_module(s, found[0], found[1], found[2])
		
		p = loaded.__dict__["page"]

		break
	except ImportError, e:
		pass

p()
