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
import cgi
import time
import random

sys.path.append(".")

from builder import Builder, getAllBuilders
from constants import config

class Response:
	def __init__(self, config):
		self.config = config
		
		self.code = "200"
		self.mesg = "OK"
	
	def __call__(self, exit=0):
		print "Status: %s" % self.code
		print "Content-type: text/plain"
		print
		print "%s" % self.mesg
		if exit:
			os._exit(0)
	
	def set_code(self, code):
		self.code = code
	
	def set_mesg(self, mesg):
		self.mesg = mesg

response = Response(config)

data = cgi.FieldStorage()

uuid = data.getfirst("uuid")
action  = data.getvalue('action')
if action == "set":
	if not uuid:
		response.set_code("406")
		response.set_mesg("UUID is not valid!")
		response(1)
	
	builder = Builder(config, uuid)
	
	key = None
	for key in [ "distcc", "duration", "hostname", "jobs", "log", "state", "package", ]:
		for value in data.getlist(key):
			builder.set(key, value)
elif action == "get":
	for key in [ "distcc", ]:
		if key == "distcc":
			for value in data.getlist(key):
				if value == "raw":
					builders = []
					jobs = "4"
					for builder in getAllBuilders():
						if uuid == builder.uuid:
							jobs = builder.jobs()
							continue
						builders.append("%s" % builder.distcc)
					string = "localhost/%s\n--randomize\n" % (jobs or "4",)
					while True:
						if not builders: break
						rand = random.randint(0, len(builders)-1)
						if builders[rand]:
							string = "%s%s\n" % (string, builders[rand],)
						builders.pop(rand)
					response.set_mesg(string)
					
else:
	response.set_code("501")
	response.set_mesg("Don't know what to do with command \"%s\"" % action)
	response(1)

response()
