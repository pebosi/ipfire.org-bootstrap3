#!/usr/bin/python

import cgitb, os, time, socket, cgi, DNS, GeoIP
cgitb.enable()

#gi = GeoIP.new(GeoIP.GEOIP_STANDARD)
gi = GeoIP.new(GeoIP.GEOIP_MEMORY_CACHE)

def print_header():
	print '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	   "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
	<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
	<head>
		<title>IPFire - Distribution</title>
		<style type="text/css">
			body { font-family: Verdana; font-size: 9pt; background-color:#f0f0f0; }
			a:link { color: black; text-decoration: none; }
			a:visited { color: black; text-decoration: none; }
			table { font-family: Verdana; font-size: 8pt; border: 1px solid; }
			td.header { background-color: #a0a0a0; text-align: center; color: white; }
			td.date { text-align: center; }
			font.installed { color: green; }
			font.deleted { color: red; }
			font.update { color: blue; }
			font.error { color: red; }
			td.online { background: green; color: white; text-align: center; }
			td.offline { background: red; color: white; text-align: center; }
		</style>
		<meta http-equiv="refresh" content="60; URL=%s?ver=%s&amp;uuid=%s" />
	</head>
	<body>
		<h1>IPFire Distribution</h1>
		<p>Made: %s</p>''' % (os.environ['SCRIPT_NAME'], ver, uuid, time.ctime())

def beautify_ip(ip):
	try:
		hostname = socket.gethostbyaddr(ip)
		string = "<b>%s</b> (%s - %s)" % (hostname[0], ip, gi.country_code_by_addr(ip))
	except socket.herror, e:
		error = "Couldn't look up name: %s" % e
		string = "<b>%s</b> (%s)" % (error, ip)
	return string
	
def beautify_time(timestamp):
	return time.strftime("%d-%m-%Y - %H:%M", time.localtime(float(timestamp)))

def get_attributes(line):
	status = ""
	pak = ""
	command = ""
	args = line.split(" ")
	ip = args[0]
	timestamp = args[1]
	if len(args) > 2:
		command = args[2]
		if len(args) > 3:
			pak = args[3]
			if len(args) > 4:
				status = args[4]

	return ip, timestamp, command, pak, status

def showuuid(uuid, ver):
	print "<h3><a href='%s?ver=%s&amp;uuid=%s#%s'>%s</a></h3>" % (os.environ['SCRIPT_NAME'], dir, uuid, uuid, uuid)
	
def summurize_addons():
	addons={}
	installed={}
	upgraded={}
	deleted={}
	oldest="9999999999999"
	newest="0000000000000"
	for dir in os.listdir("version/"):
#		print dir+"<br />"
		for uuid in os.listdir("version/"+dir):
#			print uuid+"<br />"
			f = open("version/"+dir+"/"+uuid)
			while True:
				line = f.readline()
				if len(line) == 0:
					break # EOF
				status = ""
				pak = ""
				command = ""
				args = line.split(" ")
				if oldest > args[1]:
					oldest = args[1]
				if newest < args[1]:
					newest = args[1]
				if len(args) > 2:
					command = args[2]
#					print command
				if len(args) > 3:
					pak = args[3]
#					print pak
				if len(args) > 4:
					status = args[4]
#					print status+"<br />"
				if (status == "0\n") and (command == "installed") and (dir == "2.1"):
					addons[pak] = addons.get(pak,0)+1
					installed[pak] = installed.get(pak,0)+1
				if (status == "0\n") and (command == "deleted") and (dir == "2.1"):
					addons[pak] = addons.get(pak,0)-1
					deleted[pak] = deleted.get(pak,0)+1
				if (status == "0\n") and (command == "upgraded") and (dir == "2.1"):
					upgraded[pak] = upgraded.get(pak,0)+1
			f.close()
	print "Oldest one installed - %s" % beautify_time(oldest)
	for x in range(10):
			print "&nbsp;"
	print "Latest action done - %s" % beautify_time(newest)
	print "<br /><br /><table width='50%'><tr>"

	for x in range(1,31):
			if ( x % 8 ):
				 print "<td align='center'>Core %s - %s</td>" % (x,upgraded.get("core-upgrade-" + str(x),0))
			else:
				 print "<td align='center'>Core %s - %s</td></tr><tr>" % (x,upgraded.get("core-upgrade-" + str(x),0))
	print "</table><br /><br /><table width='50%'>"

	print "<tr><td class='header'>Addon</td><td class='header'>Anzahl</td><td class='header'>Installiert</td><td class='header'>Deinstalliert</td></tr>"
	for name, nummer in sorted(addons.items()):
		print "<tr><td align='center'>"
		print name
		print "</td><td align='center'>"
		print nummer
		print "</td><td align='center'><font color=green>+"
		print installed.get(name, 0)
		print "</fond></td><td align='center'><font color=red>-"
		print deleted.get(name, 0)
		print "</td></tr>"
	print "</table>"

def showdetails(uuid, ver):
	f = open("version/"+dir+"/"+uuid)
	print "<a name='"+uuid+"' />\n<h3>"+uuid+"</h3>"
	print "<table width='70%'>"
	print "<tr><td class='header' width='70%'>IP-address<td class='header' width='30%'>Updates"
	while True:
		line = f.readline()
		if len(line) == 0:
			break # EOF
		
		ip, timestamp, command, pak, status = get_attributes(line)
		
		if command == "update\n":
			last_update = timestamp
			continue

		string = "<tr><td>"
		string += beautify_ip(ip)

		timestamp = beautify_time(timestamp)
		
		
		if command:
			string += " - <font class='%s'>%s</font> - %s" % (command, command, pak)
			if not status == "0\n":
				string += " <font class='error'>%s</font>" % status
												
		string += "</td><td class='date'>%s</td></tr>" % timestamp
		
		print string

	print "<tr><td>Last update:</td><td align='center'>%s" % beautify_time(timestamp)			
	print "</table>"
	f.close()


def summary(type):
	print "<table width='50%'>"
	print "<tr><td class='header' colspan='2'>Summary</td></tr>"
	if type == "global":
		print "<tr><td>Versions available:</td><td>",
		print os.listdir("version/"),
		print "</td></tr>"
		
		print "<tr><td>Number of total hosts:</td><td>",
		count = 0
		for dir in os.listdir("version/"):
			count += len(os.listdir("version/"+dir))
		print count,
		print "</td></tr>"

		
	print "</table>"

### HTTP-Header
#
print "Content-type: text/html"
print

form = cgi.FieldStorage()

ver  = form.getfirst('ver')
uuid = form.getfirst('uuid')

if not uuid:
	uuid = ""

print_header()

summary("global")

for dir in os.listdir("version/"):

	print "<h2><a href='%s?ver=%s&amp;uuid='>%s</a></h2>" % (os.environ['SCRIPT_NAME'], dir, dir)
	if ver == dir:
		for i in os.listdir("version/"+dir):
			if i == uuid:
				showdetails(i, dir)
			else:
				showuuid(i, dir)

summurize_addons()

print "</body></html>"
