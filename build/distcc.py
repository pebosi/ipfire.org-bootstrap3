#!/usr/bin/python

import cgitb, os, time, cgi, re, random, socket, DNS
cgitb.enable()

def print_http_header():
	print "Content-type: text/html"
	print

def print_header():
	print_http_header()	
	print '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
	   "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
	<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
	<head>
		<title>IPFire - DistccWatch</title>
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
		<meta http-equiv="refresh" content="60; URL=%s" />
	</head>
	<body>
		<h1>IPFire DistccWatch</h1>
		<p>Made: %s</p>''' % (os.environ['SCRIPT_NAME'], time.ctime())
		
def print_footer():
	print "\t</body>\n</html>"
		
def print_dcc_info():
	print "<pre>",
	print os.popen("distcc --version").read(),
	print "</pre>"

def read_hosts():
	f = open("hosts")
	hosts = []
	while True:
		line = f.readline()
		if len(line) == 0:
			hosts.sort()
			return hosts
			break #EOF
		
		if not line.startswith("#"):
			hosts.append(line.rstrip("\n"))

def process_hosts(hosts=""):
	if not hosts:
		print "You need to specify the hosts you want to check in the config file."
		return
		
	print '''<table width='66%'>
	<tr>
			<td class='header' width='68%'>Host</td>
			<td class='header' width='16%'>State</td>
			<td class='header' width='16%'>Probe</td>
	</tr>'''
	
	for hostname in hosts:
	
		state = "DOWN"
		time = "&nbsp;"
		command = "HOME=tmp DISTCC_HOSTS=\"%s\" DISTCC_VERBOSE=1 distcc probe.c -S -o /dev/null 2>&1" % hostname
		state_pattern = re.compile("on %s completed ok" % hostname)
		time_pattern = re.compile("elapsed compilation time ")

		for line in os.popen(command).readlines():
			state_result = re.search(state_pattern, line)
			time_result = re.search(time_pattern, line)
			if not state_result == None:
				state = "UP"
			if not time_result == None:
				if state == "UP":
					time = time_result.string[-10:]
			
		print "<tr><td><pre>%s</pre></td><td>%s</td><td>%s</td></tr>" % (hostname, state, time)
	
	print "</table>"

def mixup_hosts(hosts=""):
	string = ""
	while True:
		if len(hosts) == 0:
			break
			
		rand = random.randint(0, len(hosts)-1)
		host, options = re.split(re.compile(':'),hosts[rand])
		string += socket.gethostbyname(host) + ":" + options + " "
		hosts.pop(rand)
		
	print string
	
form = cgi.FieldStorage()
action  = form.getfirst('action')

if action == "raw":
	print_http_header()
	
	hosts = read_hosts()
	
	mixup_hosts(hosts)

else:

	print_header()
	print_dcc_info()
	
	hosts = read_hosts()
	
	process_hosts(hosts)
	
	print_footer()
