#!/usr/bin/python

import web.info

info = web.info.Info()

def cluster_get_info(params):
	import web.cluster
	cluster = web.cluster.Cluster(info["hosting"]["cluster"])
	return cluster.json
