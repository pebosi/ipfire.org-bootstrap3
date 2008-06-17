#!/usr/bin/python

import os
import time
import cgi

from stat import ST_MTIME
from rhpl.simpleconfig import SimpleConfigFile

DB_DIR = "db"

def format_time(seconds, use_hours=1):
	if seconds is None or seconds < 0:
		if use_hours: return '--:--:--'
		else:         return '--:--'
	else:
		seconds = int(seconds)
		minutes = seconds / 60
		seconds = seconds % 60
		if use_hours:
			hours = minutes / 60
			minutes = minutes % 60
			return '%02i:%02i:%02i' % (hours, minutes, seconds)
		else:
			return '%02i:%02i' % (minutes, seconds)

def format_number(number, SI=0, space=' '):
	"""Turn numbers into human-readable metric-like numbers"""
	symbols = ['',  # (none)
		   'k', # kilo
		   'M', # mega
		   'G', # giga
		   'T', # tera
		   'P', # peta
		   'E', # exa
		   'Z', # zetta
		   'Y'] # yotta
    
	if SI: step = 1000.0
	else: step = 1024.0

	thresh = 999
	depth = 0
	max_depth = len(symbols) - 1
    
	# we want numbers between 0 and thresh, but don't exceed the length
	# of our list.  In that event, the formatting will be screwed up,
	# but it'll still show the right number.
	while number > thresh and depth < max_depth:
		depth  = depth + 1
		number = number / step

	if type(number) == type(1) or type(number) == type(1L):
		# it's an int or a long, which means it didn't get divided,
		# which means it's already short enough
		format = '%i%s%s'
	elif number < 9.95:
		# must use 9.95 for proper sizing.  For example, 9.99 will be
		# rounded to 10.0 with the .1f format string (which is too long)
		format = '%.1f%s%s'
	else:
		format = '%.0f%s%s'
        
	return(format % (float(number or 0), space, symbols[depth]))

stage2desc = {
	"unknown" : "Dunno what the host is doing at the moment...",
	"compiling" : "The host is really hard working at the moment...",
	"error" : "Oops! The host had an error...",
	"idle" : "The host is idle at the moment...",
}

sys2desc = {
	"CPU_NAME" : "CPU model",
	"CPU_MIPS" : "Bogomips",
	"CPU_MHZ"  : "CPU MHz",
	"MEM_SIZE" : "Memory size",
} 

class Site:
	def __init__(self):
		print "Content-type: text/html"
		print	
	
	def __call__(self):
		print '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
		   "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
		<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
		<head>
			<title>IPFire - Builder</title>
			<style type="text/css">
				body { font-family: Verdana; font-size: 9pt; background-color:#f0f0f0; }
				a:link { color: black; text-decoration: none; }
				a:visited { color: black; text-decoration: none; }
				table { font-family: Verdana; font-size: 8pt; border: 1px solid; }
				td.header { background-color: #a0a0a0; text-align: left; color: white; 
						font-size: 11pt; }
				td.date { text-align: center; }
				font.installed { color: green; }
				font.deleted { color: red; }
				font.update { color: blue; }
				font.error { color: red; }
				td.log { background: pink; }
				td.update { background: darkgrey; }
				/* td.distcc { background: darkgrey; } */
				td.online { background: green; color: white; text-align: center; }
				td.offline { background: red; color: white; text-align: center; }
			</style>
			<meta http-equiv="refresh" content="90; URL=%s" />
		</head>
		<body>
			<h1>IPFire Builder</h1>
			<p>This site is for monitoring the build machines...</p>
			<p>Made: %s</p>''' % (os.environ['SCRIPT_NAME'], time.ctime())

		self.content()

		print "\t\t</body>\n</html>"
	
	def content(self):
		for builder in builders:
			builder()


class Builder:
	def __init__(self, uuid=None):
		self.uuid = uuid
		self.db = os.path.join(DB_DIR, self.uuid)
		
		if not os.path.isdir(self.db):
			os.mkdir(self.db)
		
		self.fn = {
			'state' : os.path.join(self.db, "state"),
			'distcc' : os.path.join(self.db, "distcc"),
			'hostname' : os.path.join(self.db, "hostname"),
			'build_durations' : os.path.join(self.db, "build_durations"),
			'log' : os.path.join(self.db, "log"),
			'profile' : os.path.join(self.db, "profile"),
		}
		
		self.sys = SimpleConfigFile()
		self.sys.read(self.fn['profile'])
		
		self.state = self._state()
	
	def _state(self, state="unknown"):
		"""State says what the host is doing at the moment.
			This can be:
		   	 - unknown	-	Didn't talk with host for more than two hours.
		   	 - compiling	-	Host is working
		   	 - error	-	Host had an error
			 - idle		-	Host is idle
			 - hidden       -       Host was idle or unknown for more than 12 hours"""
		
		if not state == "unknown":
			f = open(self.fn['state'], "w")
			f.write("%s\n" % state)
			f.close()

		if not os.access(self.fn['state'], os.R_OK):
			return state
		
		six_h_ago = int(time.time()) - (3600 * 6)
		twelve_h_ago = int(time.time()) - (3600 * 12)
		mtime = os.stat(self.fn['state'])[ST_MTIME]
		
		if mtime > six_h_ago:
			try:
				f = open(self.fn['state'])
				state = f.readline().rstrip("\n")
				f.close()
			except:
				pass
		elif mtime > twelve_h_ago:
			state = "hidden"

		return state
	
	def _build_durations(self, duration=None):
		"""This returns a 4x-tupel:
			First value is best build duration.
			Second value is average build duration.
			Third value is worst build duration.
			Fourth value is the whole build duration."""
		
		## set duration
		if duration:
			f = open(self.fn['build_durations'], "a")
			f.write("%s\n" % int(duration))
			f.close()
			return
		
		## get duration
		durations = []
		all_build_duration = 0
		try:
			f = open(self.fn['build_durations'])
		except IOError:
			return (None, None, None, None)
		else:
			while True:
				duration = f.readline().rstrip("\n")
				if not duration:
					break # EOF
				durations.append(int(duration))
			f.close()
			durations.sort()
			for duration in durations:
				if duration < 3600: continue
				all_build_duration += duration
			
			avg = all_build_duration / len(durations)
			
			return (durations[0], avg, durations[-1], all_build_duration)
	
	def _log(self, log=[]):
		
		if log:
			f = open(self.fn['log'], "w")
			f.write("%s\n" % log)
			f.close()
			return
		
		try:
			f = open(self.fn['log'])
			log = f.readlines()
			f.close()
		except:
			pass
		
		return log
	
	def _last_update(self):
		if not os.access(self.fn['state'], os.R_OK):
			return

		return os.stat(self.fn['state'])[ST_MTIME]
	
	def _profile_get(self, what=None):
		data = self.sys.get(what)
		if data and what.endswith("_SIZE"):
			data = format_number(int(data))
		return data or None
	
	def _profile_set(self, what):
		self.sys.set(what)
		self.sys.write(self.fn['profile'])

	def __repr__(self):
		return "<Builder %s>" % self.uuid
	
	def __call__(self):
		if self.state == "hidden":
			return
		
		self.hostname = self._profile_get("HOSTNAME")
		self.distcc = self._profile_get("DISTCC")
		self.build_durations = self._build_durations()
		self.last_update = self._last_update()

		print "<table width='66%'>"
		
		## give hostname or uuid
		print "\t<tr>"
		print "\t\t<td class='header' colspan='3' width='100%'>",
		if self.hostname:
			print self.hostname,
		else:
			print self.uuid,
		print "</td>"
		print "\t</tr>"
		
		## give state
		print "\t<tr>"
		print "\t\t<td class='state' colspan='2' width='80%'><b>",
		print stage2desc[self.state],
		print "</b></td>"
		print "\t\t<td class='state' rowspan='7' width='20%'>",
		print "<img alt='%s' width='128px' height='128px' src='/images/%s.png' />" % (self.state, self.state,),
		print "</td>"
		print "\t</tr>"
		
		## give sys info
		for key in [ "CPU_NAME", "CPU_MHZ", "CPU_MIPS", "MEM_SIZE", ]:
			print "\t<tr>"
			print "\t\t<td class='sys' width='60%'><b>",
			print sys2desc[key]
			print "</b></td>"
			print "\t\t<td class='durations' width='40%'>",
			print self._profile_get(key) or "N/A"
			print "</td>"
			print "\t</tr>"
		
		## give durations
		(min, avg, max, all) = self.build_durations
		print "\t<tr>"
		print "\t\t<td class='durations' width='60%'>",
		print "<b>Build durations</b>",
		print "</td>"
		print "\t\t<td class='durations' width='40%'>",
		if avg:
			print "<b>Average:</b> %s h<br />" % format_time(avg),
		if min:
			print "<b>Minimum:</b> %s h<br />" % format_time(min),
		if max:
			print "<b>Maximum:</b> %s h<br />" % format_time(max),
		if all:
			print "<b>As a whole:</b> %s h" % format_time(all),
		
		if not avg and not min and not max and not all:
			print "N/A",
		
		print "</td>"
		print "\t</tr>"
		
		## give distcc
		print "\t<tr>"
		print "\t\t<td class='distcc' width='60%'>",
		print "<b>Distcc capable</b>",
		print "</td>"
		print "\t\t<td class='distcc' width='40%'>",
		if self.distcc == None or self.distcc == "0":
			print "No",
		else:
			print "Yes (port: %s)" \
				% (self.distcc),
		print "</td>"
		print "\t</tr>"
		
		## give log
		if self.state == "error":
			print "\t<tr>"
			print "\t\t<td class='log' colspan='3' width='100%'>",
			for line in self._log():
				print "%s<br/>" % (line,)
			print "</td>"
			print "\t</tr>"
		
		## give lastupdate
		if self.last_update:
			print "\t<tr>"
			print "\t\t<td class='update' colspan='3' width='100%'>",
			print "Last update:",
			print time.strftime("%Y-%b-%d %I:%M %p", time.localtime(self.last_update)),
			print " - ",
			print format_time(int(time.time() - self.last_update)),
			print "ago </td>"
			print "\t</tr>"
		
		print "</table>"
		
		print "<br />"

form = cgi.FieldStorage()
action  = form.getfirst('action')

if action in [ "compiling", "error", "idle", "set" ]:
	builder = Builder(form.getfirst('uuid'))
	if not action == "set":
		builder._state(action)
	if action == "set":
		key = form.getfirst('key')
		val = form.getfirst('val')
		if key == "duration":
			builder._build_durations(val)
		else:
			builder._profile_set((key, val))
	elif action == "error":
		log = form.getfirst('log')
		builder._log(log)
else:
	builders = []
	for uuid in os.listdir(DB_DIR):
		if not os.path.isdir(os.path.join(DB_DIR, uuid)): continue
		builders.append(Builder(uuid))
	
	site = Site()
	site()
