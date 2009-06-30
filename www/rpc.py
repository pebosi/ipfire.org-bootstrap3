#!/usr/bin/python

import cgi
import simplejson as json

import web.cluster


form = cgi.FieldStorage()

if form.getfirst("type") == "cluster":
	nodes = []
	ret = {}
	cluster = web.cluster.Cluster("minerva.ipfire.org")
	for node in cluster.nodes:
		tmp = { "hostname" : node.hostname,
			"address"  : node.address,
			"arch"     : node.arch,
			"jobs"     : node.jobs,
			"load"     : node.load,
			"speed"    : node.speed, }
		
		nodes.append(tmp)
	ret["nodes"] = nodes
	ret["cluster"] = { "load"  : cluster.load, }
	print json.dumps(ret, sort_keys=True, indent=4)

