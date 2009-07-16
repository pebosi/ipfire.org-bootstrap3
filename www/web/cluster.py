#!/usr/bin/python

import telnetlib

import simplejson as json

class Node(object):
	def __init__(self, hostname, address, arch, speed, jobs, load):
		self.hostname = hostname
		self.address = address
		self.arch = arch
		self.speed = speed

		(jobs_cur, jobs_max) = jobs.split("/")
		if jobs_cur > jobs_max:
			jobs_cur = jobs_max
		self.jobs = "%s/%s" % (jobs_cur, jobs_max)

		self.load = int(load) / 10 # in percent
	
	def __str__(self):
		return self.hostname
	
	def __repr__(self):
		return "<Node %s>" % self.hostname

	def print_node(self):
		print "Hostname : %s" % self.hostname
		print "  Address: %s" % self.address
		print "  Arch   : %s" % self.arch
		print "  Speed  : %s" % self.speed
		print "  Jobs   : %s" % self.jobs
		print "  Load   : %s" % self.load

class Cluster(object):
	def __init__(self, scheduler, port=8766):
		self.scheduler = scheduler
		self.port = port

		self._nodes = None
	
	def command(self, command):
		connection = telnetlib.Telnet(self.scheduler, self.port)
		connection.read_until("quit.\n")
		connection.write("%s\nquit\n" % command)
		return connection.read_until("200 done").split("\n")

	@property
	def load(self):
		if not self.nodes:
			return 0
		load = 0
		for node in self.nodes:
			load += node.load
		load /= len(self.nodes)
		return load
	
	@property
	def jobs(self):
		jobs_cur = jobs_max = 0
		for node in self.nodes:
			jobs_cur += int(node.jobs.split("/")[0])
			jobs_max += int(node.jobs.split("/")[1])
		return "%s/%s" % (jobs_cur, jobs_max)

	@property
	def nodes(self):
		if self._nodes:
			return self._nodes
		ret = []
		data = self.command("listcs")
		for line in data:
			if line.startswith("  "): continue
			if not line.startswith(" "): continue
			(a, hostname, address, arch, speed, jobs, load) = line.split(" ")
			address = address.strip("()")
			arch = arch.strip("[]")
			speed = speed.split("=")[1]
			jobs = jobs.split("=")[1]
			load = load.split("=")[1]
			ret.append(Node(hostname, address, arch, speed, jobs, load))
		self._nodes = ret
		return ret

	@property
	def json(self, *args):
		nodes = []
		ret = {}
		for node in self.nodes:
			tmp = { "hostname" : node.hostname,
					"address"  : node.address,
					"arch"     : node.arch,
					"jobs"     : node.jobs,
					"load"     : node.load,
					"speed"    : node.speed, }
			nodes.append(tmp)
		ret["nodes"] = nodes
		ret["cluster"] = { "load"  : self.load,
						   "jobs"  : self.jobs, }
		#return json.dumps(ret)
		return ret


if __name__ == "__main__":		
	cluster = Cluster("minerva.ipfire.org")
	print cluster.command("listcs")
	for node in cluster.nodes:
		node.print_node()
