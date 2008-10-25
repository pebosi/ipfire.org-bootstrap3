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
					height: 115px;
					text-align: center;
					background: #E0E0E0;
					border: 1px solid #999;
					padding-top: 10px;
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
		if self.builders:
			print """\
				<p>
					""",
			for builder in self.builders:
				print builder,
			print """
				</p>"""
		for i in self.config["nightly_url"]:
			print """\
				<p><a href="%s" target="_blank">%s</a></p>""" % (i, i,)
		print """\
			</div>"""

		self.content()

		print "\t\t</body>\n</html>"

	def content(self):
		if self.builders:
			count = 0
			print """\
			<div id="content">"""
			for builder in self.builders:
				builder(count)
				count += 1
			print """\
			</div>"""

class Box:
	def __init__(self, builder):
		self.builder =  builder
	
	def __call__(self, count):
		print """\
				<a name="%s"></a>
				<div class="box" style="%s">"""\
				% (self.builder.hostname(), state2style[self.builder.state()],)
		print """\
					<div class="infobox">"""
		self.distccinfo()
		self.package()
		self.time()
		print """\
					</div>"""
		self.header()
		self.stateinfo()
		self.durations()
		if self.builder.state() == "error":
			self.log()
		print """\
				</div>"""
	
	def __str__(self):
		return """<a href="#%(hostname)s">%(hostname)s</a>""" % { "hostname" : self.builder.hostname(), }

	def header(self):
		print """\
					<p class="boxheader">
						%(hostname)s <span>[%(uuid)s]</span>
					</p>
					<!-- <img class="right" src="/images/%(state)s.png" /> -->""" \
				% { "hostname" : self.builder.hostname(),
					"state"    : self.builder.state(),
					"uuid"     : self.builder.uuid, }
	
	def package(self):
		if self.builder.state() in [ "compiling", "error", ]:
			print """\
						<p class="package">%s</p>"""\
				% self.builder.package()
	
	def time(self):
		print """\
						<p>%s</p>""" \
				% time.ctime(float(self.builder.state.time()))
	
	def stateinfo(self):
		if self.builder.state() in [ "compiling", "error", "idle", ]:
			print """\
					<p class="desc">%s</p>""" \
				 % statedesc[self.builder.state()]
	
	def durations(self):
		print """\
					<p>Average Build Duration: %s</p>""" \
				% format_time(self.builder.duration.get_avg())
		if self.builder.state() == "compiling":
			print """\
					<p>ETA: %s</p>""" \
				% self.builder.duration.get_eta(self.builder.state.time())
	
	def distccinfo(self):
		state = self.builder.distcc.ping()
		port = self.builder.distcc()
		if port == "0":
			state = False
			port = "disabled"
		print """\
						<p class="%s">Distcc: %s</p>""" \
				% (ping2class[state], port,)
	
	def log(self):
		log = self.builder.log()
		if log:
			print """\
					<div class="log">
						<p>"""
			for i in log:
				print "%s<br />" % (i.rstrip("\n"),)
			print """\
						</p>
					</div>
			"""

site = Site(config)

boxes = []
for builder in getAllBuilders(3):
	boxes.append(Box(builder))

site(boxes)
