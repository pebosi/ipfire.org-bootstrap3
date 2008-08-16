#!/usr/bin/python

import os
import random
import urllib2
import urlparse
import cgi
from mimetypes import guess_type

debug = None #open("debug.log", "a")

hosts = (
#			PRIO SCHEME  HOSTNAME               PATH
			( 2, "http", "mirror1.ipfire.org",  "/",),
			( 4, "http", "mirror2.ipfire.org",  "/",),
			( 8, "http", "www.rowie.at",        "/ipfire/",),
			( 8, "http", "ipfire.earl-net.com", "/",),
			( 8, "http", "ipfire.kbarthel.de",  "/",),
			( 8, "http", "ipfire.1l0v3u.com",   "/",),
			( 4, "http", "hex2.sv-altikon.ch",  "/ipfire/",),
)

def rnd(servers):
	return random.randint(0, len(servers)-1)

def servefile(file):
	mimetype = guess_type(file)[0] or "text/plain"
	f = open(file, "rb")
	size = os.fstat(f.fileno()).st_size
	print "Status: 200 OK"
	print "Content-Type:", mimetype
	if size:
		print "Content-Length:", size
	print
	print f.read(),
	f.close()

class Server:
	def __init__(self, scheme="http", hostname=None, path=None, priority=0):
		self.hostname = hostname
		self.path     = path

		self.scheme   = scheme
		self.priority = priority

	def url(self):
		return "%s://%s%s" % (self.scheme, self.hostname, self.path)

	def __str__(self):
		return self.url()

	def __repr__(self):
		return "<%s.%s %s>" % (__name__, __class__, self.__str__())

	def noping(self):
		return os.system("ping -c1 -w1 %s &>/dev/null" % self.hostname)

	def file(self, file):
		ret = None
		try:
			f = urllib2.urlopen("%s" % urlparse.urljoin(self.url(), file))
		except (urllib2.HTTPError, urllib2.URLError), e:
			if debug:
				debug.write("ERR %s %s\n" % (self.url(), e))
		else:
			ret = f.geturl()
			f.close()
		return ret

class Servers:
	def __init__(self):
		self.servers = []
		self.prio_servers = []

	def __call__(self):
		return self.all()

	def all(self):
		return self.servers

	def shuffled(self):
		tmp = []
		for server in self.all():
			for priority in range(0, server.priority):
				tmp.append(server)
		return tmp

	def one(self):
		servers = self.shuffled()
		return servers[rnd(servers)]

	def add(self, server):
		self.servers.append(server)

	def rem(self, server):
		tmp = []
		for host in self.all():
			if not host == server:
				tmp.append(host)
		self.servers = tmp

# main()
servers = Servers()
for (priority, scheme, hostname, path) in hosts:
	servers.add(Server(scheme=scheme, hostname=hostname, path=path, priority=priority))

file = cgi.FieldStorage().getfirst("file")

while servers.all():
	server = servers.one()

	if server.noping():
		servers.rem(server)
		continue

	url = server.file(file)
	if not url:
		servers.rem(server)
		continue

	print "Status: 302 Moved Temporarily"
	print "Location:", url
	print "Pragma: no-cache"
	print

	if debug:
		debug.write("OK  %s\n" % url)

	break
else:
	if os.access(file, os.R_OK):
		servefile(file)
	else:
		print "Status: 404 Not Found"
		print "Pragma: no-cache"
		print

		if debug:
			debug.write("ERR %s wasn't found on any server" % file)

if debug:
	debug.close()
