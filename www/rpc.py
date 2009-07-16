#!/usr/bin/python

import cgi
import simplejson as json

from rpc_functions import *

form = cgi.FieldStorage()
method = form.getfirst("method")
id     = form.getfirst("id")
params = form.getlist("params")

methods = { "cluster_get_info" : cluster_get_info }

if method and methods.has_key(method):
	print json.dumps({ "version": "1.1",
					   "id": id or "null",
					   "result" : methods[method](params),
					   "error" : "null", },
					 sort_keys=True, indent=4)
