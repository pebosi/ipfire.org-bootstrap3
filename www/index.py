#!/usr/bin/python

import os
import re
import cgi

sites = (
			("ipfire.org", ("www.ipfire.org", None)),
			("www.ipfire.org", (None, cgi.FieldStorage().getfirst("file") or "index")),
			("source.ipfire.org", ("www.ipfire.org", "source")),
			("tracker.ipfire.org", ("www.ipfire.org", "tracker")),
			("download.ipfire.org", ("www.ipfire.org", "download")),
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
			location += "/%s/%s" % (destination[1], language,)
		break

print "Location: %s" % location
print # End the header
