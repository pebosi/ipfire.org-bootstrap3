#!/usr/bin/python

import os
import time

import web
import web.elements
import web.javascript

from web.info import Info
info = Info()

def size(file):
	size = os.path.getsize(file)
	suffixes = [("B",2**10), ("K",2**20), ("M",2**30), ("G",2**40), ("T",2**50)]
	for suf, lim in suffixes:
		if size > lim:
			continue
		else:
			return "%s%s" % (round(size/float(lim/2**10),2), suf)


class Build(object):
	def __init__(self, path, basedir, url):
		self.path = path
		self.basedir = basedir
		self.url = os.path.join(url, path[len(basedir)+1:])

		# Read .buildinfo
		f = open("%s/.buildinfo" % path)
		self.info = f.readlines()
		f.close()

	def __repr__(self):
		return "<Build %s>" % self.path
	
	def __cmp__(self, other):
		return cmp(float(other.get("date")), float(self.get("date")))
	
	def get(self, key):
		key = key.upper() + "="
		for line in self.info:
			if line.startswith(key):
				return line.split("=")[1].rstrip("\n")
		return None

	@property
	def hostname(self):
		return self.get("hostname")
	
	@property
	def release(self):
		return self.get("release")
	
	@property
	def date(self):
		return time.strftime("%Y-%m-%d %H:%M", time.localtime(float(self.get("date"))))
	
	@property
	def arch(self):
		return self.get("arch")
	
	@property
	def duration(self):
		if not self.get("duration") or self.get("duration") == "":
			return "--:--"
		return time.strftime("%H:%M", time.gmtime(float(self.get("duration"))))
	
	@property
	def iso(self):
		return self.get("iso")
	
	@property
	def packages(self):
		path = "%s/packages_%s" % (self.path, self.arch,)
		if not os.path.exists(path):
			return []
		return os.listdir(path)
	
	@property
	def pxe(self):
		dir = "/srv/www/ipfire.org/pxe"
		for iso in os.listdir(dir):
			# Skip non-iso files
			if not iso.endswith(".iso"):
				continue
			if os.readlink(os.path.join(dir, iso)) == os.path.join(self.path, self.iso):
				return "[PXE]"
		return ""


class Content(web.Content):
	def __init__(self):
		web.Content.__init__(self)
	
		self.builds = []
		for location in info["nightly_builds"]:
			# Only process correctly configured locations
			if not location.has_key("path") or not location.has_key("url"):
				continue

			# Continue if path does not exist
			if not os.path.exists(location["path"]):
				continue

			for (dir, subdirs, files) in os.walk(location["path"]):
				if not os.path.exists("%s/.buildinfo" % dir):
					continue
				self.builds.append(Build(dir, location["path"], location["url"]))
		self.builds.sort()

	def __call__(self, lang):
		today = time.strftime("%A, %Y-%m-%d", time.localtime())
		last_day = ""

		ret = """<h3>Nightly builds</h3>
				<table id="builds">
					<!-- <thead>
						<tr>
							<th>&nbsp;</th>
							<th>Release</th>
							<th>Host &amp; Date</th>
							<th>Download</th>
						</tr>
					</thead> -->
					<tbody>"""
		
		# if there are no builds
		if not self.builds:
			ret += """<tr class="headline"><td colspan="6">There are currently no builds available.</td></tr>"""

		else:
			for build in self.builds:
				# write headers
				day = time.strftime("%A, %Y-%m-%d", time.localtime(float(build.get("date"))))
				if day != last_day:
					if day == today:
						ret += """<tr class="headline"><td colspan="5">Today</td></tr>"""
					else:
						ret += """<tr class="headline"><td colspan="5">&nbsp;<br />&nbsp;<br />%s</td></tr>""" % day
					last_day = day

				ret += """<tr class="build">
							<td><a href="%s" target="_blank">""" % build.url

				if day == today:
					ret += """<img src="/images/icons/ipfire.png" alt="IPFire" /></a></td>"""
				else:
					ret += """<img src="/images/icons/ipfire_sw.png" alt="IPFire" /></a></td>"""

				ret += """\
							<td>&nbsp;<br />
								<strong>%(release)s</strong> (%(arch)s) %(pxe)s<br />
								<a href="%(url)s/%(iso)s">%(iso)s</a> %(size_iso)s</td>
							<td>&nbsp;<br />
								%(hostname)s<br />
								%(date)s [%(duration)sh]</td>
							<td class="packages">%(num_packages)s <a href="%(url)s/packages_%(arch)s/" target="_blank">[PAKS]</a></td>
						</tr>""" % { "release"  : build.release,
									 "hostname" : build.hostname,
									 "arch"     : build.arch, 
									 "date"     : build.date,
									 "duration" : build.duration,
									 "url"      : build.url,
									 "iso"      : build.iso,
									 "size_iso" : size(os.path.join(build.path, build.iso)),
									 "num_packages" : len(build.packages),
									 "pxe"      : build.pxe }

		ret += """\
					</tbody>
				</table>"""

		return ret


page = web.Page()
page.content = Content()
page.sidebar = web.elements.DevelopmentSidebar()

### Disabled because it looks awful
#page.javascript = web.javascript.Javascript(jquery=1)
#page.javascript.jquery_plugin("alternate")
#page.javascript.write("""
#	<script type="text/javascript">
#		$(function() {
#			$("#builds tbody tr.build").alternate({odd:'odd', even:'even'});
#		});
#	</script>
#""")
