#!/usr/bin/python

import os
import re
import cgi

# Check language...
language = "en"
try:
	if re.search(re.compile("^de(.*)"), os.environ["HTTP_ACCEPT_LANGUAGE"]):
		language = "de"
except KeyError:
	pass

index = cgi.FieldStorage().getfirst("file") or "index"

sites = (
			("ipfire.org", ("www.ipfire.org", None)),
			("www.ipfire.org", (None, index + "/%s" % language)),
			("source.ipfire.org", ("www.ipfire.org", "source/" + language)),
			("tracker.ipfire.org", ("www.ipfire.org", "tracker/" + language)),
			("download.ipfire.org", ("www.ipfire.org", "download/" + language)),
			("people.ipfire.org", ("wiki.ipfire.org", language + "/people/start")),
		)

print "Status: 302 Moved"
print "Pragma: no-cache"

location = ""

for (servername, destination) in sites:
	if servername == os.environ["SERVER_NAME"]:
		if destination[0]:
			location = "http://%s" % destination[0]
		if destination[1]:
			location += "/%s" % destination[1]
		break

print "Location: %s" % location
print # End the header
