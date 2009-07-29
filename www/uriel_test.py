#!/usr/bin/python

import sys
import urlgrabber
import urllib
import simplejson as json

data = {}
id = None

for arg in sys.argv[1:]:
	if not id:
		id = data["id"] = arg
		continue

	try:
		item, value = arg.split("=")
	except:
		print "Cannot split arg: ", arg
		continue
	
	value = value.strip("\"")

	data[item] = value

if not data:
	print "No data to send."
	sys.exit(0)

request = { "id"     : "null",
			"method" : "uriel_send_info",
			"params" : json.dumps(data), }

g = urllib.urlopen("http://www.ipfire.org/rpc.py", data=urllib.urlencode(request))
print g.read()
g.close()
