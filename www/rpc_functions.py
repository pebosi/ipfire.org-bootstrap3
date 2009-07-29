#!/usr/bin/python

import time

import web.info

info = web.info.Info()

def cluster_get_info(params):
	import web.cluster
	cluster = web.cluster.Cluster(info["hosting"]["cluster"])
	return cluster.json

def uriel_send_info(params):
	import web.urieldb
	db = web.urieldb.Urieldb()
	
	id = None
	items = {}
	for (item, value) in params.items():
		if item == "id":
			id = value
		if item not in web.urieldb.allowed_items:
			continue
		items[item] = value

	# We need an id
	if not id:
		return

	for item, value in items.items():
		db.set(id, item, value)

	# Save date of last modification
	db.set(id, "date", "%s" % int(time.time()))
