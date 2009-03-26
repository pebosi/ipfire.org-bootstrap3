#!/usr/bin/python

import os
import cgi

from web.http import HTTPResponse

for language in ("de", "en",):
	if os.environ["HTTP_ACCEPT_LANGUAGE"].startswith(language):
		break

site = cgi.FieldStorage().getfirst("site") or "index"

sites = {	"ipfire.org"			: "www.ipfire.org",
			"www.ipfire.org"		: "/%s/%s" % (language, site,),
			"source.ipfire.org"		: "http://www.ipfire.org/%s/source" % language,
			"tracker.ipfire.org"	: "http://www.ipfire.org/%s/tracker" % language,
			"torrent.ipfire.org"	: "http://www.ipfire.org/%s/tracker" % language,
			"download.ipfire.org"	: "http://www.ipfire.org/%s/download" % language,
			"people.ipfire.org"		: "http://wiki.ipfire.org/%s/people/start" % language, }

httpheader = []

try:
	httpheader.append(("Location", sites[os.environ["SERVER_NAME"]]))
except KeyError:
	httpheader.append(("Location", sites["www.ipfire.org"]))

h = HTTPResponse(302, httpheader, None)
h.execute()
