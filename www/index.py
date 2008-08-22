#!/usr/bin/python

import os
import re
import cgi

sites = (
			("ipfire.org", ("www.ipfire.org", None)),
			("www.ipfire.org", (None, cgi.FieldStorage().getfirst("file") or "index.shtml")),
			("source.ipfire.org", (None, "source.shtml")),
			("tracker.ipfire.org", (None, "tracker.shtml")),
			("download.ipfire.org", (None, "download.shtml")),
		)

# Check language...
language = "en"
try:
	if re.search(re.compile("^de(.*)"), os.environ["HTTP_ACCEPT_LANGUAGE"]):
		language = "de"
except KeyError:
	pass

print "Status: 302 Moved"
print "Pragma: no-cache"

location = ""

for (servername, destination) in sites:
	if servername == os.environ["SERVER_NAME"]:
		if destination[0]:
			location = "http://%s" % destination[0]
		if destination[1]:
			location += "/%s/%s" % (language, destination[1])
		break

print "Location: %s" % location
print # End the header
