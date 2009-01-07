#!/usr/bin/python
###############################################################################
#                                                                             #
# IPFire.org - A linux based firewall                                         #
# Copyright (C) 2008  Michael Tremer & Christian Schmidt                      #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                             #
###############################################################################

import os
import sys
import time

sys.path.append(".")

from builder import Builder, getAllBuilders
from constants import *

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

class Site:
	def __init__(self, config):
		self.builders = None
		self.config = config
		print "Content-type: text/html"
		print
	
	def __call__(self, builders=None):
		self.builders = builders
		print """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
		   "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
		<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
		<head>
			<title>%(title)s</title>
			<style type="text/css">
				* {
					margin: auto;
					padding: 0;
					text-decoration: none;
					outline: none;
				}
				body {
					font-family: Verdana;
					font-size: 90%%;
					background-color:#f9f9f9;
				}
				h1 {
					text-decoration: underline;
				}
				#header {
					width: 800px;
					text-align: center;
					background: #E0E0E0;
					border: 1px solid #999;
					padding-top: 10px;
					padding-bottom: 5px;
				}
				#content {
					padding-top: 10px;
					width: 800px;
				}
				div.box {
					padding: 5px;
					margin: 10px 0 10px 0;
					/* height: 80px; */
					border: 1px solid;
				}
				div.infobox {
					float: right;
					width: 240px;
				}
				div.log {
					background: #e55;
					border: 1px dotted;
					margin-top: 12px;
					/* visibility: hidden; */
				}
				div.log p {
					font-family: Courier New;
				}
				div.footer {
				}
				div.footer p {
					text-align: center;
					font-size: 5px;
				}
				p {
					margin: 2px;
				}
				p.boxheader {
					font-weight: bold;
				}
				p.online {
					color: green;
				}
				p.offline {
					color: red;
				}
				p.package {
					font: bold;
					font-size: 150%%;
				}
				img.right {
					float: right;
				}
				p.desc {
					text-decoration: bold;
				}
				a:link {
					color: black; text-decoration: none;
				}
				a:visited {
					color: black; text-decoration: none;
				}
			</style>
			<meta http-equiv="refresh" content="90; URL=%(script)s" />
		</head>
		<body>
			<div id="header">
				<h1>IPFire Builder</h1>""" % self.config
		for i in self.config["nightly_url"]:
			print """\
				<p><a href="%s" target="_blank">%s</a></p>""" % (i, i,)
		print """\
			</div>"""

		self.content()

		print "\t\t</body>\n</html>"

	def content(self):
		if self.builders:
			print """\
			<div id="content">"""
			for builder in self.builders:
				builder()
			print """\
			</div>"""

class Box:
	def __init__(self, builder):
		self.builder = builder
		self.points = POINTS_UNKNOWN
	
	def __cmp__(self, other):
		if self.points > other.points:
			return -1
		elif self.points == other.points:
			return 0
		elif self.points < other.points:
			return 1

	def __str__(self):
		return """<a href="#%(hostname)s">%(hostname)s</a>""" % { "hostname" : self.builder.hostname(), }

	def open_bigbox(self):
		print """<a name="%s"></a><div class="box" style="%s">""" \
			% (self.builder.hostname(), state2style[self.builder.state()],)

	def open_infobox(self):
		print """<div class="infobox">"""

	def close_bigbox(self):
		print """</div>"""

	close_infobox = close_bigbox

	def header(self):
		print """<p class="boxheader">%(hostname)s <span>[%(uuid)s]</span></p>""" \
			% { "hostname" : self.builder.hostname(),
				"state"    : self.builder.state(),
				"uuid"     : self.builder.uuid, }
	
	def package(self):
		if self.builder.state() in [ "compiling", "error", ]:
			print """\
						<p class="package">%s</p>"""\
				% self.builder.package()
	
	def time(self):
		print """<p>%s</p>""" \
			% time.ctime(float(self.builder.state.time()))
	
	def stateinfo(self):
		print """<p class="desc">%s</p>""" \
			% statedesc[self.builder.state()]
	
	def durations(self):
		print """<p>Average Build Duration: %s</p>""" \
			% format_time(self.builder.duration.get_avg())
		if self.builder.state() == "compiling":
			print """<p>ETA: %s</p>""" \
				% self.builder.duration.get_eta(self.builder.state.time())
	
	def distccinfo(self):
		state = self.builder.distcc.ping()
		port = self.builder.distcc()
		if port == "0":
			state = False
			port = "disabled"
		print """<p class="%s">Distcc: %s</p>""" \
				% (ping2class[state], port,)
	
	def log(self):
		log = self.builder.log()
		if log:
			print """<div class="log"><p>"""
			for i in log:
				if i:
					print "%s<br />" % (i.rstrip("\n"),)
			print """</p></div>"""

	def footer(self):
		print """<div class="footer"><p>cpu: %s - target: %s - jobs: %s</p></div>""" \
			% (self.builder.cpu(), self.builder.target(), self.builder.jobs(),)

class BoxCompiling(Box):
	def __init__(self, builder):
		Box.__init__(self, builder)
		self.points = POINTS_COMPILING

	def __call__(self):
		self.open_bigbox()
		self.open_infobox()
		self.distccinfo()
		self.package()
		self.time()
		self.close_infobox()
		self.header()
		self.stateinfo()
		self.durations()
		self.footer()
		self.close_bigbox()

class BoxError(Box):
	def __init__(self, builder):
		Box.__init__(self, builder)
		self.points = POINTS_ERROR

	def __call__(self):
		self.open_bigbox()
		self.open_infobox()
		self.distccinfo()
		self.package()
		self.time()
		self.close_infobox()
		self.header()
		self.stateinfo()
		self.durations()
		self.log()
		self.footer()
		self.close_bigbox()

class BoxDistcc(Box):
	def __init__(self, builder):
		Box.__init__(self, builder)
		self.points = POINTS_DISTCC

	def __call__(self):
		self.open_bigbox()
		self.open_infobox()
		self.distccinfo()
		self.time()
		self.close_infobox()
		self.header()
		self.stateinfo()
		self.durations()
		self.footer()
		self.close_bigbox()

class BoxIdle(Box):
	def __init__(self, builder):
		Box.__init__(self, builder)
		self.points = POINTS_IDLE

	def __call__(self):
		self.open_bigbox()
		self.open_infobox()
		self.distccinfo()
		self.time()
		self.close_infobox()
		self.header()
		self.stateinfo()
		self.durations()
		self.footer()
		self.close_bigbox()

site = Site(config)

boxes = []
for builder in getAllBuilders():
	box = None
	if builder.state() == "compiling":
		box = BoxCompiling(builder)
	elif builder.state() == "error":
		box = BoxError(builder)
	elif builder.state() == "idle":
		box = BoxIdle(builder)
	elif builder.state() == "distcc":
		if builder.distcc() == "0":
			continue
		box = BoxDistcc(builder)
	if box:
		boxes.append(box)

boxes.sort()
site(boxes)
