#!/usr/bin/python

import simplejson
import subprocess

class Item(object):
	def __init__(self, **args):
		self.args = args
	
	def __getattr__(self, key):
		return self.args[key]

	def __getitem__(self, key):
		return self.args[key]
		
	def __setitem__(self, key, val):
		self.args[key] = val

def size(s):
	suffixes = ["B", "K", "M", "G", "T",]
	
	idx = 0
	while s >= 1024 and idx < len(suffixes):
		s /= 1024
		idx += 1

	return "%.0f%s" % (s, suffixes[idx])

def json_loads(s):
	return simplejson.loads(s.decode("utf-8"))

def _stringify(d):
	ret = {}
	for key in d.keys():
		ret[str(key)] = d[key]
	return ret

def ping(host, count=5, wait=10):
	cmd = subprocess.Popen(
		["ping", "-c%d" % count, "-w%d" % wait, host],
		stdout = subprocess.PIPE,
		stderr = subprocess.PIPE,
	)

	latency = None

	out, error = cmd.communicate()

	for line in out.split("\n"):
		if not line.startswith("rtt"):
			continue

		line = line.split()
		if len(line) < 4:
			break

		rtts = line[3].split("/")
		if len(rtts) < 4:
			break

		latency = "%.1f" % float(rtts[1])

	return latency


if __name__ == "__main__":
	print ping("www.ipfire.org")
	print ping("www.rowie.at")
