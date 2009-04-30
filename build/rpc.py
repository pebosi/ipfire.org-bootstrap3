#!/usr/bin/python
###############################################################################
#                                                                             #
# IPFire.org - A linux based firewall                                         #
# Copyright (C) 2008,2009 Michael Tremer & Christian Schmidt                  #
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

sys.path.append(".")

from builder import Builder, getAllBuilders
from constants import config

ALLOWED_ACTIONS_SET = (	"distcc", "duration", "hostname", "jobs", "log", "state",
						"package", "target", "toolchain", "cpu", "machine", "system",)
ALLOWED_ACTIONS_GET = ( "distcc",)

def run(uuid, action):
	myself = Builder(config, uuid)

	if action == "get":
		for key in ALLOWED_ACTIONS_GET:
			if key == "distcc":
				for value in data.getlist(key):
					if value == "raw":
						builders = getAllBuilders()
						print "--randomize"
						for builder in builders:
							# Print "localhost" for ourself
							if myself.uuid == builder.uuid:
								print "localhost"
							else:
								if ((myself.toolchain() == builder.toolchain()) and \
									(myself.machine() == builder.machine()) and \
									(myself.target() == builder.target())):
									print "%s" % (builder.distcc,)

	elif action == "set":
		for key in ALLOWED_ACTIONS_SET:
			for value in data.getlist(key):
				print myself.set(key, value)

data = cgi.FieldStorage()

print "Status: 200 - OK" # We always send okay.
print

try:
	uuid   = data.getfirst("uuid")
	action = data.getfirst("action")
	if uuid and action:
		run(uuid, action)
except SystemExit:
	pass
