#!/usr/bin/python

import cgitb, sys, os, time, cgi
cgitb.enable()

### HTTP-Header
#
print "Content-type: text/html"
print

form = cgi.FieldStorage()

uuid = form.getfirst('uuid')
ver  = form.getfirst('ver')
ipak = form.getfirst('ipak')
dpak = form.getfirst('dpak')
upak = form.getfirst('upak')
ret  = form.getfirst('return')

if not uuid or not ver:
	sys.exit(1) # Exit when the arguments are not set

if not os.path.exists("version/"+ver):
	os.mkdir("version/"+ver)

zeit = time.time()
string = "%s %d" % (os.environ['REMOTE_ADDR'], zeit)

if ipak:
	string += " installed %s %s" % (ipak, ret)
elif dpak:
	string += " deleted %s %s" % (dpak, ret)
elif upak:
	string += " upgraded %s %s" % (upak, ret)
else:
	string += " update"

string += "\n"

f = open("version/"+ver+"/"+uuid, "a")
f.write(string)
f.close()

for file in os.listdir("version/"+ver):
	time_diff = zeit - os.path.getmtime("version/"+ver+"/"+file)
	if time_diff > 259200:
		os.remove("version/"+ver+"/"+file)

print "200 OK"
