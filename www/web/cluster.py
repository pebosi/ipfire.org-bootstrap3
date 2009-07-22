#!/usr/bin/python

import os
import telnetlib

import simplejson as json

class Node(object):
	def __init__(self, hostname, address, arch, speed, jobcount, load, installing):
		self.hostname = hostname
		self.address = address
		self.arch = arch
		self.speed = speed
		self.installing = installing

		(jobs_cur, jobs_max) = jobcount.split("/")
		if jobs_cur > jobs_max:
			jobs_cur = jobs_max
		self.jobcount = "%s/%s" % (jobs_cur, jobs_max)

		self.load = int(load) / 10 # in percent
		
		self.jobs = []
	
	def __str__(self):
		return self.hostname
	
	def __repr__(self):
		return "<Node %s>" % self.hostname

	def print_node(self):
		print "Hostname : %s" % self.hostname
		print "  Address: %s" % self.address
		print "  Arch   : %s" % self.arch
		print "  Speed  : %s" % self.speed
		print "  Jobs   : %s" % self.jobcount
		print "  Load   : %s" % self.load

class Job(object):
	def __init__(self, id, status, submitter, compiler, file):
		self.id = id
		self.status = status
		self.submitter = submitter
		self.compiler = compiler
		self.file = file


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
	def jobcount(self):
		jobs_cur = jobs_max = 0
		for node in self.nodes:
			jobs_cur += int(node.jobcount.split("/")[0])
			jobs_max += int(node.jobcount.split("/")[1])
		return "%s/%s" % (jobs_cur, jobs_max)

	@property
	def nodes(self):
		if self._nodes:
			return self._nodes
		ret = []
		data = self.command("listcs")
		node = None
		for line in data:
			if not line.startswith(" "):
				continue # does not belong to the data

			if line.startswith("  ") and node: # Job
				(a, b, c, id, status, submitter, compiler, file) = line.split(" ")
				submitter = submitter[4:]
				compiler = compiler[3:]
				file = os.path.basename(file)
				job = Job(id, status, submitter, compiler, file)
				node.jobs.append(job)

			elif line.startswith(" "): # Node
				installing = False
				a = line.split(" ")
				if len(a) > 7:
					installing = True
					line = " ".join(a[0:7])
				
				(a, hostname, address, arch, speed, jobcount, load) = line.split(" ")
				address = address.strip("()")
				arch = arch.strip("[]")
				speed = speed[6:]
				jobcount = jobcount[5:]
				load = load[5:]
				node = Node(hostname, address, arch, speed, jobcount, load, installing)
				ret.append(node)
			
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
					"jobcount" : node.jobcount,
					"load"     : node.load,
					"speed"    : node.speed,
					"installing" : node.installing,}
			jobs = []
			for job in node.jobs:
				jobs.append({ "id"        : job.id,
							  "status"    : job.status,
							  "submitter" : job.submitter,
							  "compiler"  : job.compiler,
							  "file"      : job.file, })
			tmp["jobs"] = jobs
			nodes.append(tmp)
		ret["nodes"] = nodes
		ret["cluster"] = { "load"     : self.load,
						   "jobcount" : self.jobcount, }
		return ret


if __name__ == "__main__":		
	cluster = Cluster("minerva.ipfire.org")
	print cluster.command("listcs")
	for node in cluster.nodes:
		node.print_node()
