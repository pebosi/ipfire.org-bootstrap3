#!/usr/bin/python

import cgi
import simplejson as json

from rpc_functions import *

form = cgi.FieldStorage()
method = form.getfirst("method")
id     = form.getfirst("id")

params = None
param_string = form.getfirst("params")
if param_string:
	params = json.loads(param_string)

methods = { "cluster_get_info" : cluster_get_info,
			"uriel_send_info"  : uriel_send_info, }

if method and methods.has_key(method):
	print json.dumps({ "version": "1.1",
					   "id": id or "null",
					   "result" : methods[method](params),
					   "error" : "null", },
					 sort_keys=True, indent=4)
