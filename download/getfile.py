#!/usr/bin/python

# This is a short script for spread our files...

import cgi, random, urllib2, sys

def redirect(url):
	print 'Status: 302 Moved Temporarily'
	print 'Location:', url
	print 'Pragma: no-cache'
	print 'Content-Type: text/html'
	print

def notfound():
	print 'Status: 404 Not Found'
	print 'Pragma: no-cache'
	print
	
def selectserver(filename):
	servers = []
	f = open("mirrorlist")
	while True:
		line = f.readline()
		if len(line) == 0:
			break # EOF
		line = line.rstrip('\n')
		servers.append(line)
	f.close()
	
	while True:
		if len(servers) == 0:
			url = "None"
			break
		rand = random.randint(0, len(servers)-1)
		url = "%s/%s" % (servers[rand], cgi.escape(filename))
		try:			
			req = urllib2.Request(url)
			req.add_header('User-Agent', 'IPFire/DownloadScript-1.0')
			urllib2.urlopen(req)
		except urllib2.HTTPError, e:
			servers.pop(rand)
		except urllib2.URLError, e:
			servers.pop(rand)
		else:
			break
	return url

form = cgi.FieldStorage()
filename  = form.getfirst('file')

url = selectserver(filename)

if url == "None":
	notfound()
else:
	redirect(url)
